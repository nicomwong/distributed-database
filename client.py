
import socket
import threading
import signal
import queue
import sys

from Operation import Operation
from TimeoutException import TimeoutException

class Client:

    basePort = 7000
    serverBasePort = 8000
    numServers = 3

    nominationTimeout = 4   # Timeout for receiving a nomination result response
    queryResponseTimeout = 5     # Timeout for receiving a response after sending a query
    
    def __init__(self, clientID):
        cls = self.__class__

        # Address variables
        self.ID = clientID
        self.port = cls.basePort + self.ID

        # Query/response variables
        self.leaderAddress = (socket.gethostbyname(socket.gethostname() ), cls.serverBasePort + 1)    # First leader hint is Server 1
        self.operationQueue = queue.Queue()
        self._response = None

    def start(self):
        # Setup my socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind( (socket.gethostname(), self.port) )
        print(f"Started client on port {self.port}")

        # Concurrently handle incoming messages
        threading.Thread(target=self.handleIncomingMessages, daemon=True).start()

        # Concurrently process the operation queue
        threading.Thread(target=self.processOperationQueue, daemon=True).start()

    def processOperationQueue(self):
        cls = self.__class__
    
        while True:
            # Wait until an operation needs to be sent
            while not len(self.operationQueue):
                continue

            #################################
            ### Nominate a new leader ###
            #################################

            self.nominateNextLeader()

            ##############################################
            ### Start sending operations to the leader ###
            ##############################################
            
            signal.alarm(cls.queryResponseTimeout)  # Timeout for a query response

            while len(self.operationQueue):
                self.sendServer(self.operationQueue.queue[0] )  # Send operation    [TODO] Send req ID with query

                try:
                    queryResponse = self.waitForResponse()

                    # Received a response, so...
                    signal.alarm(0) # Cancel the timer
                    self.operationQueue.get()   # Pop the operation queue

                    print(f"[CLIENT] Received query response: {queryResponse}")
                    
                except TimeoutException:
                    print("Timed out with no query response.")
                    break   # Assume the leader failed, so restart the process

    def nominateNextLeader(self):
        """
        Returns once a successful nomination response is received.
        If it returns, then self.leaderAddress is set correctly.
        """
        
        # Nominate servers until one responds with a successful election result
        while True:
            print("Nominating next server to be leader.")
            self.response = None    # Clear the response holder
            signal.alarm(timeout)   # Set the timeout

            self.sendServer("leader")   # Send nomination

            try:
                electionResult = self.waitForResponse()
                signal.alarm(0) # Cancel the timer

                if electionResult == "success":
                    return

                elif electionResult == "failure":
                    # Move onto another server
                    serverID = self.leaderAddress[1] - cls.serverBasePort
                    nextServerPort = cls.serverBasePort + 1 + serverID % cls.numServers
                    self.leaderAddress = (socket.gethostbyname(socket.gethostname() ), nextServerPort)
                    print("Election failed.")
                    continue
                    
                else:
                    print("Received unknown nomination result")
                    continue
                    
            except TimeoutException:
                print("Timed out with no nomination response.")
                continue
          
    def waitForResponse(self):
        "Blocks until a response is received (from the leader)"
        while self._response == None:    # Blocks until self.response is set
            pass
        return self._response

    def sendServer(self, *msgTokens):
        self.sendMessage(msgTokens, self.leaderServerAddress)

    def sendMessage(self, msgTokens, destinationAddr):
        msgTokenStrings = [ str(token)
                            for token in msgTokens]  # Convert tokens to strings
        msg = '-'.join(msgTokenStrings)  # Separate tokens by delimiter

        self.sock.sendto(msg.encode(), destinationAddr)
        print(f"Sent message \"{msg}\" to server at port {destinationAddr[1]}")

    def handleIncomingMessages(self):
        while True:
            data, addr = self.sock.recvfrom(4096)
            msg = data.decode()
            print(f"Received message \"{msg}\" from machine at {addr}")

            # Parse message into components
            msgArgs = msg.split('-')
            msgClass = msgArgs[0]

            if addr == self.leaderServerAddress:
                # Communicating with leader

                if len(msgArgs) == 2:
                    if msgClass == "response":
                        self.response = msgArgs[1]

                    else:
                        print("Invalid message format")

            else:
                print("Invalid message format")


def handleUserInput():
    while True:
        cmdArgs = input().split()

        cmd = cmdArgs[0]

        if len(cmdArgs) == 2:
            if cmd == "get":    # get <key>
                key = cmdArgs[1]
                op = Operation.Get(key)
                client.operationQueue.put(op)
                # print("New operation queue: ", operationQueue.queue)
        
        elif len(cmdArgs) == 3:
            if cmd == "put":    # put <key> <value>
                key = cmdArgs[1]
                value = cmdArgs[2]
                op = Operation.Put(key, value)
                client.operationQueue.put(op)
                # print("New operation queue: ", operationQueue.queue)

            elif cmd == "send": # send <msg> <port>
                msg = cmdArgs[1]
                recipient = (socket.gethostname(), int(cmdArgs[2]) )

                client.sendMessage( (msg,), recipient)
            
        else:
            print("Invalid command.")

if len(sys.argv) != 2:
    print(f"Usage: python3 {sys.argv[0]} clientID")
    sys.exit()

clientID = int(sys.argv[1])

# Start client
client = Client(clientID)
client.start()

# Handle stdin
handleUserInput()
