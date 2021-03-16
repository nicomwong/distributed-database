
import socket
import threading
import queue
import sys

from Operation import Operation

class Client:

    # Testing vars
    debugMode = False

    basePort = 7000
    serverBasePort = 8000
    numServers = 3

    nominationTimeout = 10  # Timeout for receiving a nomination result response
    queryTimeout = 12       # Timeout for receiving a response after sending a query
    
    def __init__(self, clientID):
        cls = self.__class__

        # Address variables
        self.ID = clientID
        self.port = cls.basePort + self.ID

        # Query variables
        self.leaderAddress = (socket.gethostbyname(socket.gethostname() ), cls.serverBasePort + 1)    # First leader hint is Server 1
        self.leaderIsValid = False
        self.operationQueue = queue.Queue()
        self.requestID = (0, self.port)

        # Response variables
        self._response = None

    def start(self):
        # Setup my socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind( (socket.gethostname(), self.port) )
        self.printLog(f"Started client on port {self.port}")

        # Concurrently handle incoming messages
        threading.Thread(target=self.handleIncomingMessages, daemon=True).start()

        # Concurrently process the operation queue
        threading.Thread(target=self.processOperationQueue, daemon=True).start()

    def processOperationQueue(self):
        cls = self.__class__
    
        while True:
            # Wait until an operation needs to be sent
            while not self.operationQueue.qsize():
                continue

            # Nominate a new leader if there is no valid leader currently
            if not(self.leaderIsValid):
                self.nominateNextLeader()

            # Start sending operations to the leader
            while self.operationQueue.qsize():
                self._response = None    # Clear the response holder

                self.printLog(f"Sending request {self.requestID} to leader")
                self.sendToLeader("request", self.operationQueue.queue[0], self.requestID)  # Send operation to leader and req ID

                terminate = False   # Thread termination flag
                timeoutThread = threading.Thread(target=self.waitForResponse, args=(lambda:terminate,), daemon=True)
                timeoutThread.start()
                timeoutThread.join(self.queryTimeout)

                # Check if timed out
                if timeoutThread.is_alive():   # Timed out
                    self.printLog("Timed out waiting for a query response")
                    self.leaderAddress = self.nextServer()
                    self.leaderIsValid = False
                    terminate = True
                    break   # Assume the leader failed, so restart

                # Received query response from the leader
                queryResponse = self._response

                self.requestID = (self.requestID[0] + 1, self.requestID[1])    # Increment request number

                self.operationQueue.get()   # Pop it from the queue

                self.printLog(f"Received query response: {queryResponse}")

    def nominateNextLeader(self):
        """
        Blocks until a successful nomination response is received.
        Once it returns, self.leaderAddress is correctly set.
        """
        
        # Nominate servers until one responds with a successful election result
        while True:
            self._response = None    # Clear the response holder

            self.printLog(f"Nominating {self.leaderAddress[1]} to be leader")
            self.sendToLeader("leader")   # Send nomination

            # Start a thread for timeout
            terminate = False    # Thread termination flag
            timeoutThread = threading.Thread(target=self.waitForResponse, args=(lambda:terminate,), daemon=True)
            timeoutThread.start()
            timeoutThread.join(self.nominationTimeout)
            
            # Check if timed out
            if timeoutThread.is_alive():   # Timed out
                self.printLog("Timed out waiting for an election result")
                self.leaderAddress = self.nextServer()  # Move onto another server
                terminate = True
                continue

            # Received nomination response from server
            electionResult = self._response

            if electionResult == "success":
                self.printLog(f"Received election result: {electionResult}")
                # self.leaderAddress is now correctly set
                self.leaderIsValid = True
                return

            elif electionResult == "failure":
                self.leaderAddress = self.nextServer()  # Move onto another server
                continue
                
            else:
                self.printLog("Received unknown nomination result")
                continue
          
    def nextServer(self):
        "Returns the address of the next server to nominate as leader"
        cls = self.__class__
        serverID = self.leaderAddress[1] - cls.serverBasePort
        nextServerPort = cls.serverBasePort + 1 + serverID % cls.numServers
        return (socket.gethostbyname(socket.gethostname() ), nextServerPort)

    def waitForResponse(self, terminate):
        """
        Blocks until a response is received (from the leader) or the terminate flag is set to True.
        Once it returns, self._response holds the response.
        """
        while not(terminate() ) and self._response is None:
            continue

    def sendToLeader(self, *msgTokens):
        self.sendMessage(msgTokens, self.leaderAddress)

    def sendMessage(self, msgTokens, destinationAddr):
        msgTokenStrings = [ str(token)
                            for token in msgTokens]  # Convert tokens to strings
        msg = '-'.join(msgTokenStrings)  # Separate tokens by delimiter

        self.sock.sendto(msg.encode(), destinationAddr)
        if self.__class__.debugMode:
            print(f"Sent message \"{msg}\" to server at port {destinationAddr[1]}")

    def handleIncomingMessages(self):
        while True:
            data, addr = self.sock.recvfrom(4096)
            msg = data.decode()
            if self.__class__.debugMode:
                print(f"Received message \"{msg}\" from machine at {addr}")

            # Communicating with leader or nominee
            self._response = msg

    def printLog(self, string):
        "Prints the input string with the client ID prefixed"
        print(f"[CLIENT {self.ID}] {string}")

def handleUserInput():
    while True:
        cmdArgs = input().split()

        cmd = cmdArgs[0]

        try:
            if len(cmdArgs) == 2:
                if cmd == "get":    # get <key>
                    key = eval(cmdArgs[1])
                    op = Operation.Get(key)
                    client.operationQueue.put(op)

                elif cmd == "print":
                    varName = cmdArgs[1]
                    if varName == "operationQueue":
                        print(f"{varName}: {client.operationQueue.queue}")
            
            elif len(cmdArgs) == 3:
                if cmd == "put":    # put <key> <value>
                    key = eval(cmdArgs[1])
                    value = eval(cmdArgs[2])
                    op = Operation.Put(key, value)
                    client.operationQueue.put(op)

                elif cmd == "send": # send <msg> <port>
                    msg = cmdArgs[1]
                    recipient = (socket.gethostname(), int(cmdArgs[2]) )

                    client.sendMessage( (msg,), recipient)
                
            else:
                print("Invalid command.")
        
        except Exception as e:
            print(e)

if len(sys.argv) != 2:
    print(f"Usage: python3 {sys.argv[0]} clientID")
    sys.exit()

clientID = int(sys.argv[1])

# Start client
client = Client(clientID)
client.start()

# Handle stdin
handleUserInput()
