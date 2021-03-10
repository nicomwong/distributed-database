
import socket
import threading
import sys
import threading
import time

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
        return self == other or self > other


class Server:

    # Class vars
    basePort = 8000
    numServers = 3

    def __init__(self, serverID):
        cls = self.__class__

        # My address
        self.ID = serverID
        self.port = cls.basePort + self.ID

        # Main Paxos variables
        self.ballotNum = BallotNum(0, self.ID, 0)
        self.acceptNum = BallotNum(0, self.ID, 0)
        self.acceptVal = None
        self.myVal = None

        # Election phase variables
        self.valsAllNone = True
        self.highestB = BallotNum(-1, -1, -1)
        self.valWithHighestB = None
        self.promiseCount = -1

        # Collect addresses of other servers
        self.serverAddresses = []
        for i in range(cls.numServers - 1):
            serverPort = cls.basePort + 1 + ( (self.ID + i) % cls.numServers)
            serverAddr = (socket.gethostbyname(socket.gethostname() ), serverPort)
            self.serverAddresses.append(serverAddr)
            # print("Added outgoing server address", serverAddr)

        # Setup my socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind( (socket.gethostname(), self.port) )
        print("Started server at port", self.port)

        # Concurrently handle receiving messages
        threading.Thread(target=self.handleIncomingMessages, daemon=True).start()

    def sendMessage(self, msgTokens, destinationAddr):
        msgTokenStrings = [ str(token)
                            for token in msgTokens]  # Convert tokens to strings
        msg = '-'.join(msgTokenStrings)  # Separate tokens by delimiter

        self.sock.sendto(msg.encode(), destinationAddr)
        print(f"Sent message \"{msg}\" to server at port {destinationAddr[1]}")

    def broadcastToServers(self, *msgTokens):
        for addr in self.serverAddresses:
            self.sendMessage(msgTokens, addr)

    def handleIncomingMessages(self):

        while True:
            data, addr = self.sock.recvfrom(4096)  # Blocks until a message arrives
            msg = data.decode()
            print(f"Received message \"{msg}\" from machine at {addr}")

            msgTokens = msg.split('-')

            # Determine whether from client or server
            if addr in self.serverAddresses:
                # From server

                # Prepare
                if msgTokens[0] == "prepare":
                    bal = eval(msgTokens[1])

                    if bal >= self.ballotNum and bal.depth >= self.ballotNum.depth:
                        self.ballotNum = bal
                        self.sendMessage(("promise", self.ballotNum, self.acceptNum, self.acceptVal), addr)

                # Promise
                if msgTokens[0] == "promise":
                    self.promiseCount += 1

                    balNum = eval(msgTokens[1])
                    b = eval(msgTokens[2])
                    val = eval(msgTokens[3])

                    # Check if all vals are None
                    self.valsAllNone = self.valsAllNone and (val is None)

                    # Eventually, this gets the val with the highest b
                    if b > self.highestB:
                        self.highestB = b
                        self.valWithHighestB = val

            else:
                # From client
                if msgTokens[0] == "leader":
                    self.ballotNum.num += 1
                    threading.Thread(target=self.electionPhase, daemon=True).start()

    def electionPhase(self):
        cls = self.__class__

        # Reset election phase variables
        self.valsAllNone = True
        self.highestB = BallotNum(-1, -1, 0)
        self.valWithHighestB = None
        self.promiseCount = 1  # Initially 1 since it accepts itself

        # Broadcast prepare
        self.broadcastToServers("prepare", self.ballotNum)

        # Wait timeout
        time.sleep(5)
        print(f"Checking promise count. promiseCount = {self.promiseCount}")

        if self.promiseCount > cls.numServers / 2:
            # Received majority
            print("I am now the leader!")
            # print(f"self.valsAllNone: {self.valsAllNone}")
            if self.valsAllNone:
                pass
                # self.myVal will be set in self.processOperationQueue

            else:
                self.myVal = self.valWithHighestB

            # Broadcast accept
            self.broadcastToServers("accept", self.ballotNum, self.myVal)

        else:
            print("I lost the election")
            pass

def handleUserInput():
    while True:
        cmdArgs = input().split()

        cmd = cmdArgs[0]

        if len(cmdArgs) == 1:
            if cmd == "debug":
                DEBUG()

        elif len(cmdArgs) == 2:
            if cmd == "broadcast":
                msg = cmdArgs[1]
                server.broadcastToServers(msg)

        elif len(cmdArgs) == 3:
            if cmd == "send":    # send <msg> <port>
                msg = cmdArgs[1]
                recipient = (socket.gethostname(), int(cmdArgs[2]))

                server.sendMessage( (msg,), recipient)

def DEBUG():
    print(f"num of running threads: {threading.active_count()}")
    print(f"promiseCount: {server.promiseCount}")

# Parse cmdline args
if len(sys.argv) != 2:
    print(f"Usage: python3 {sys.argv[0]} serverID")
    sys.exit()

serverID = int(sys.argv[1])

server = Server(serverID)   # Start the server

# Handle stdin
handleUserInput()
