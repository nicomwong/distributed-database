
import socket
import threading
import multiprocessing  # For timeouts
import queue
import sys

from Operation import Operation

class Client:

    basePort = 7000
    serverBasePort = 8000
    numServers = 3

    nominationTimeout = 4   # Timeout for receiving a nomination result response
    queryTimeout = 5     # Timeout for receiving a response after sending a query
    
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
            while not self.operationQueue.qsize():
                continue

            # Nominate a new leader
            self.nominateNextLeader()

            # Start sending operations to the leader
            while len(self.operationQueue):
                self.sendLeader(self.operationQueue.queue[0] )  # Send operation    [TODO] Send req ID with query

                timeoutProcess = multiprocessing.Process(target=self.waitForResponse, daemon=True)
                timeoutProcess.start()
                timeoutProcess.join(self.queryTimeout)

                # Check if timed out
                if timeoutProcess.is_alive():   # Timed out
                    print("Timed out waiting for a query response")
                    self.leaderAddress = self.nextServer()
                    timeoutProcess.terminate()
                    continue    # Assume the leader failed, so restart

                # Received query response from the leader
                queryResponse = self._response

                self.operationQueue.get()   # Pop it from the queue

                print(f"[CLIENT] Received query response: {queryResponse}")

    def nominateNextLeader(self):
        """
        Blocks until a successful nomination response is received.
        Once it returns, self.leaderAddress is correctly set.
        """
        
        # Nominate servers until one responds with a successful election result
        while True:
            # print(f"Nominating the server at {self.leaderAddress} to be leader.")
            self._response = None    # Clear the response holder

            self.sendLeader("leader")   # Send nomination

            # Start a thread for timeout
            timeoutProcess = multiprocessing.Process(target=self.waitForResponse, daemon=True)
            timeoutProcess.start()
            timeoutProcess.join(self.nominationTimeout)
            
            # Check if timed out
            if timeoutProcess.is_alive():   # Timed out
                print("Timed out waiting for an election result")
                self.leaderAddress = self.nextServer()  # Move onto another server
                timeoutProcess.terminate()
                continue

            # Received nomination response from server
            electionResult = self._response

            if electionResult == "success":
                return

            elif electionResult == "failure":
                self.leaderAddress = self.nextServer()  # Move onto another server
                continue
                
            else:
                print("Received unknown nomination result")
                continue
          
    def nextServer(self):
        "Returns the address of the next server to nominate as leader"
        cls = self.__class__
        serverID = self.leaderAddress[1] - cls.serverBasePort
        nextServerPort = cls.serverBasePort + 1 + serverID % cls.numServers
        return (socket.gethostbyname(socket.gethostname() ), nextServerPort)

    def waitForResponse(self):
        """
        Blocks until a response is received (from the leader).
        Once it returns, self._response holds the response.
        """
        while self._response is None:    # Blocks until self._response is set
            continue

    def sendLeader(self, *msgTokens):
        self.sendMessage(msgTokens, self.leaderAddress)

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

            if addr == self.leaderAddress:
                # Communicating with leader or nominee
                self._response = msg

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
