
import queue
from collections import defaultdict

import socket
import threading
import sys
import os
import time
import pprint

from DictServer import *


class BallotNum:

    def __init__(self, num, PID, depth):
        self.num = num
        self.PID = PID
        self.depth = depth

    def __repr__(self):
        return f"BallotNum({self.num}, {self.PID}, {self.depth})"

    # Operators
    def __lt__(self, other):
        return (self.num, self.PID) < (other.num, other.PID)

    def __eq__(self, other):
        return (self.num, self.PID) == (other.num, other.PID)

    def __ne__(self, other):
        return not(self == other)

    def __gt__(self, other):
        return not(self < other) and not(self == other)

    def __ge__(self, other):
        return not(self < other)


class Server:

    # Testing vars
    debugMode = False

    # Class vars
    basePort = 8000
    numServers = 3
    electionTimeout = 6 # Timeout to wait for majority promises after broadcasting prepare
    replicationTimeout = 6  # Timeout to wait for majority accepted after broadcasting accept (leader-only)

    def __init__(self, serverID):
        cls = self.__class__

        # My address
        self.ID = serverID
        self.ip = socket.gethostbyname(socket.gethostname() )
        self.port = cls.basePort + self.ID

        # Backup file
        self.backupBlockchainFileName = f"server{self.ID}_blockchain"

        # Simulation variables
        self.propagationDelay = 2
        self.brokenLinks = set()

        # Data structures
        self.blockchain = Blockchain()
        self.kvstore = KVStore()
        self.requestQueue = queue.Queue()  # Queue of blocks to propose when leader

        # Main Paxos variables
        self.ballotNum = BallotNum(0, self.ID, 0)
        self.isLeader = False
        self.leaderHintAddress = (socket.gethostbyname(socket.gethostname() ), cls.basePort + 1)  # Default hint is Server 1

        # Election phase variables
        self.valsAllNone = True
        self.highestB = BallotNum(-1, -1, -1)
        self.valWithHighestB = None
        self.promiseCount = -1
        self.nominatorAddress = None    # Address of client who nominated me

        # Replication phase variables
        self.acceptNum = BallotNum(0, self.ID, 0)
        self.acceptVal = None
        self.myVal = None
        self.acceptedCount = defaultdict(lambda: 0)

        # Get server addresses
        self.serverAddresses = []
        for i in range(cls.numServers):
            serverPort = cls.basePort + 1 + ( (self.ID + i) % cls.numServers)
            serverAddr = (socket.gethostbyname(socket.gethostname() ), serverPort)
            self.serverAddresses.append(serverAddr)
            # print("Added outgoing server address", serverAddr)

    def start(self):
        # Setup my socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((socket.gethostname(), self.port))
        self.printLog(f"Started server at port {self.port}")

        # Recover from stable storage (save file) if there is one
        saveFileName = f"server{self.ID}_blockchain"
        if os.path.isfile(saveFileName):
            self.blockchain = Blockchain.read(saveFileName)
            self.kvstore = self.blockchain.generateKVStore()

        # Concurrently handle receiving messages
        threading.Thread(target=self.handleIncomingMessages,
                         daemon=True).start()

        threading.Thread(target=self.processBlockQueue, daemon=True).start()

    def cleanExit(self):
        "Cleanly exits by closing all open sockets and files"
        self.sock.close()

    def electionPhase(self):
        cls = self.__class__

        # Update ballotNum fields
        self.ballotNum.depth = self.blockchain.depth
        self.ballotNum.num += 1

        # Reset election phase variables
        self.valsAllNone = True
        self.highestB = BallotNum(-1, -1, 0)
        self.valWithHighestB = None
        self.promiseCount = 0

        # Broadcast prepare
        self.printLog(f"Broadcasting \"prepare\" with {self.ballotNum}")
        self.broadcastToServers("prepare", self.ballotNum)

        # Start a thread for timeout
        terminate = False    # Thread termination flag
        timeoutThread = threading.Thread(target=self._waitForMajorityPromises, args=(lambda:terminate,), daemon=True)
        timeoutThread.start()
        timeoutThread.join(cls.electionTimeout)

        # Check if timed out
        if timeoutThread.is_alive():   # Timed out
            self.printLog("Timed out waiting for a majority of promises. I lost the election")
            self.sendMessage( ("failure",), self.nominatorAddress)   # Respond failure nomination to the nominator
            terminate = True
            return

        # Received majority
        self.printLog("Received a majority of promises. I am now the leader!")
        self.isLeader = True
        self.sendMessage( ("success",), self.nominatorAddress)  # Respond successful nomination to the nominator
        self.printLog("Broadcasting \"I am leader\" to other servers")
        self.broadcastToServers("I am leader", me=False)  # Broadcast election result to the other servers

        if not self.valsAllNone:
            # Inherited a request
            inheritedRequest = (self.valWithHighestB.operation, self.valWithHighestB.requestID)
            self.requestQueue.put(inheritedRequest)

    def _waitForMajorityPromises(self, terminate):
        "Blocks until a majority of promises are received"
        cls = self.__class__
        while not(terminate() ) and self.promiseCount <= cls.numServers / 2:
            continue

    def processBlockQueue(self):
        while True:
            if self.isLeader:
                if not self.requestQueue.empty():
                    currRequest = self.requestQueue.get()
                    if not self.blockchain._list:
                        prevBlock = None
                    else:
                        prevBlock = self.blockchain._list[-1]

                    self.myVal = Block.Create(currRequest[0], currRequest[1], prevBlock)
                    self.replicationPhase()
            else:
                # Flushes requestQueue, clients will handling resending any unanswered requests
                self.requestQueue.queue.clear()

    def replicationPhase(self):
        cls = self.__class__

        # Update ballotNum depth
        self.ballotNum.depth = self.blockchain.depth

        # Broadcast accept to servers
        self.printLog(f"Broadcasting \"accept\" with {self.ballotNum}")
        self.broadcastToServers("accept", self.ballotNum, self.myVal)

        # Wait for a majority of accepted messages but with a timeout
        terminate = False
        timeoutThread = threading.Thread(target=self._waitForMajorityAccepted, args=(self.myVal, lambda:terminate,), daemon=True)
        timeoutThread.start()
        timeoutThread.join(cls.replicationTimeout)

        # Check if timed out
        if timeoutThread.is_alive():   # Timed out
            self.printLog("Timed out waiting for a majority of accepted. Relinquishing leadership.")
            self.isLeader = False
            terminate = True
            return

    def _waitForMajorityAccepted(self, val, terminate):
        "Blocks until a majority of accepted are received for val"
        cls = self.__class__
        while self.acceptedCount[val] <= cls.numServers / 2:
            continue

    def sendMessage(self, msgTokens, destinationAddr):
        """
        Sends a message with components msgTokens to destinationAddr with a simulated self.propagationDelay second delay (Non-blocking).
        If the link to destinationAddr is broken, then nothing will arrive.
        """
        cls = self.__class__

        msgTokenStrings = [str(token) for token in msgTokens]  # Convert tokens to strings
        msg = '-'.join(msgTokenStrings)  # Separate tokens by delimiter

        if cls.debugMode:
            print(f"Sent message \"{msg}\" to machine at port {destinationAddr[1]}")

        if destinationAddr[1] in self.brokenLinks:
            # For simulating broken links, the message is sent but never arrives
            return

        threading.Thread(target=self._sendMessageWithDelay, args=(msg, destinationAddr), daemon=True).start()

    def _sendMessageWithDelay(self, msg, destinationAddr):
        "Only meant to be used in conjunction with self.sendMessage() to unblock with simulated delay"
        time.sleep(self.propagationDelay)
        self.sock.sendto(msg.encode(), destinationAddr)

    def broadcastToServers(self, *msgTokens, me=True):
        "Broadcasts msgTokens to every server, including myself iff me=True"
        
        for addr in self.serverAddresses:
            if addr == (self.ip, self.port) and me == False:
                continue
            self.sendMessage(msgTokens, addr)

    def handleIncomingMessages(self):
        cls = self.__class__

        while True:
            # Blocks until a message arrives
            data, addr = self.sock.recvfrom(4096)

            if addr[1] in self.brokenLinks:
                # For simulating broken links, the message never arrives
                continue

            msg = data.decode()
            if cls.debugMode:
                print(f"Received message \"{msg}\" from machine at {addr}")

            msgArgs = msg.split('-')
            msgType = msgArgs[0]

            # Determine whether from client or server
            if addr in self.serverAddresses:
                # From server

                # Prepare
                if msgType == "prepare":
                    bal = eval(msgArgs[1])

                    if bal >= self.ballotNum and bal.depth >= self.blockchain.depth:
                        self.ballotNum = bal
                        self.sendMessage( ("promise", self.ballotNum, self.acceptNum, self.acceptVal), addr)
                        self.printLog(f"Responding promise to {addr[1]} for ballot {self.ballotNum}")

                # Promise
                elif msgType == "promise":
                    self.promiseCount += 1

                    balNum = eval(msgArgs[1])
                    b = eval(msgArgs[2])
                    val = eval(msgArgs[3])

                    # Check if all vals are None
                    self.valsAllNone = self.valsAllNone and (val is None)

                    # Eventually, this gets the val with the highest b
                    if b > self.highestB:
                        self.highestB = b
                        self.valWithHighestB = val

                # Receive "I am leader" from a server
                elif msg == "I am leader":
                    self.printLog(f"Received \"I am leader\" from {addr[1]}. Setting my leader hint and relinquishing my leader status")
                    self.leaderHintAddress = addr
                    self.isLeader = False

                elif msgType == "accept":
                    b = eval(msgArgs[1])
                    val = eval(msgArgs[2])

                    if b >= self.ballotNum and b.depth >= self.ballotNum.depth:
                        self.acceptNum = b
                        self.acceptVal = val
                        self.blockchain.accept(val, b.depth)
                        self.blockchain.write(self.backupBlockchainFileName)
                        self.broadcastToServers("accepted", b, val) # For N^2 "accepted" message optimization of Decide phase
                        self.printLog(f"Received accept from {addr[1]} for ballot {self.ballotNum}. Broadcasting \"accepted\"")

                elif msgType == "accepted": # accepted-BallotNum(...)-Block(...)
                    b = eval(msgArgs[1])
                    val = eval(msgArgs[2])

                    self.acceptedCount[val] += 1

                    if self.acceptedCount[val] == cls.numServers // 2 + 1:
                        # Received majority "accepted"
                        self.printLog(f"Received majority accepted. Deciding on value for request {val.requestID} and depth {b.depth}")

                        # Decide on val
                        self.blockchain.decide(val, b.depth)
                        self.blockchain.write(self.backupBlockchainFileName)
                        self.kvstore.processBlock(val)

                        # Leader sends the query answer to the requester
                        if self.isLeader:
                            answer = self._getAnswer(val.operation)
                            requesterAddr = (socket.gethostbyname(socket.gethostname() ), val.requestID[1])
                            self.sendMessage( (answer,), requesterAddr)
                            self.printLog(f"Sent the answer {answer} to the requester at {requesterAddr[1]}")
                        
                        # Reset Accept-phase variables
                        self.acceptNum = BallotNum(0, self.ID, 0)
                        self.acceptVal = None

            else:
                # From client
                if msgType == "leader":
                    self.printLog(f"Nominated to be leader by client at {addr[1]}")
                    self.nominatorAddress = addr    # Track the nominator for responding
                    threading.Thread(target=self.electionPhase, daemon=True).start()

            # From client or server

            # Receiving a request
            if msgType == "request":    # request-Operation()-reqID
                op = eval(msgArgs[1])
                requestID = eval(msgArgs[2])
                request = (op, requestID)
                self.printLog(f"Received request {requestID} from {addr[1]}")

                if self.isLeader:
                    self.requestQueue.put(request)
                else:
                    # Forward request to leader hint
                    self.printLog(f"Forwarding request {requestID} to server at {self.leaderHintAddress[1]}")
                    self.sendMessage(msgArgs, self.leaderHintAddress)

    def _getAnswer(self, operation):
        "Returns the answer of performing operation on self.kvstore"
        if operation.type == "get":
            if operation.key in self.kvstore._dict:
                return self.kvstore.get(operation.key)
            else:
                return "KEY_DOES_NOT_EXIST"

        elif operation.type == "put":
            return "success"

        else:
            return None

    def printLog(self, string):
        "Prints the input string with the server ID prefixed"
        print(f"[SERVER {self.ID}] {string}")


def handleUserInput():
    while True:
        cmdArgs = input().split()

        cmd = cmdArgs[0]

        if len(cmdArgs) == 1:
            if cmd == "failProcess":
                server.printLog("Crashing...")
                server.cleanExit()
                sys.exit()

            elif cmd == "debug":
                DEBUG()

        elif len(cmdArgs) == 2:
            if cmd == "failLink":
                dstPort = int(cmdArgs[1])
                if dstPort not in server.brokenLinks:
                    server.brokenLinks.add(dstPort)
                    server.printLog(f"Broke the link to {dstPort}")
                else:
                    server.printLog(f"The link to {dstPort} is already broken")

            elif cmd == "fixLink":
                dstPort = int(cmdArgs[1])
                if dstPort in server.brokenLinks:
                    server.brokenLinks.remove(dstPort)
                    server.printLog(f"Fixed the link to {dstPort}")
                else:
                    server.printLog(f"The link to {dstPort} is not broken")

            elif cmd == "broadcast":
                msg = cmdArgs[1]
                server.broadcastToServers(msg)

            elif cmd == "print":
                varName = cmdArgs[1]
                print(f"{varName}:")

                if varName == "brokenLinks" or varName == "bl":
                    pprint.pprint(server.brokenLinks)

                elif varName == "blockchain" or varName == "bc":
                    pprint.pprint(server.blockchain._list)

                elif varName == "depth":
                    print(server.blockchain.depth)

                elif varName == "kvstore" or varName == "kv":
                    pprint.pprint(server.kvstore._dict)

                elif varName == "requestQueue" or varName == "rq":
                    pprint.pprint(server.requestQueue.queue)

                elif varName == "serverList" or varName == "sl":
                    print(server.serverAddresses)

                else:
                    print("Does not exist")

        elif len(cmdArgs) == 3:
            if cmd == "send":    # send <msg> <port>
                msg = cmdArgs[1]
                recipient = (socket.gethostname(), int(cmdArgs[2]))

                server.sendMessage((msg,), recipient)


def DEBUG():
    print(f"num of running threads: {threading.active_count()}")
    print(f"promiseCount: {server.promiseCount}")


# Parse cmdline args
if len(sys.argv) != 2:
    print(f"Usage: python3 {sys.argv[0]} serverID")
    sys.exit()

serverID = int(sys.argv[1])

server = Server(serverID)   # Start the server
server.start()

# Handle stdin
handleUserInput()
