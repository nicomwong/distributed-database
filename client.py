
import socket
import threading
import queue
import sys

from Operation import Operation

class Client:

    basePort = 7000
    
    def __init__(self, clientID):
        cls = self.__class__

        # Address variables
        self.ID = clientID
        self.port = cls.basePort + self.ID
        
        # Setup my socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind( (socket.gethostname(), self.port) )
        print(f"Started client on port {self.port}")

        # Concurrently handle incoming messages
        threading.Thread(target=self.handleIncomingMessages, daemon=True).start()

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

def handleUserInput():
    while True:
        cmdArgs = input().split()

        cmd = cmdArgs[0]

        if len(cmdArgs) == 2:
            if cmd == "get":    # get <key>
                key = cmdArgs[1]
                op = Operation.Get(key)
                operationQueue.put(op)
                # print("New operation queue: ", operationQueue.queue)
        
        elif len(cmdArgs) == 3:
            if cmd == "put":    # put <key> <value>
                key = cmdArgs[1]
                value = cmdArgs[2]
                op = Operation.Put(key, value)
                operationQueue.put(op)
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

operationQueue = queue.Queue()

# Handle stdin
handleUserInput()
