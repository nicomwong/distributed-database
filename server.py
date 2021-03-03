
import socket
import threading
import sys
import threading
import time

from DictServer import *


class BallotNum:

    def __init__(self, seqNum, PID, depth):
        self.seqNum = seqNum
        self.PID = PID
        self.depth = depth

    def __repr__(self):
        return f"BallotNum({self.seqNum}, {self.PID}, {self.depth})"

    # Operators
    def __lt__(self, other):
        return (self.seqNum, self.PID) < (other.seqNum, other.PID)

    def __eq__(self, other):
        return (self.seqNum, self.PID) == (other.seqNum, other.PID)

    def __ne__(self, other):
        return not(self == other)

    def __gt__(self, other):
        return not(self < other) and not(self == other)

    def __ge__(self, other):
        return self == other or self > other


def sendMessage(msgTokens, destination):
    # print("msgTOkens:", msgTokens)
    msgTokenStrings = [str(token)
                       for token in msgTokens]  # Convert tokens to strings
    msg = '-'.join(msgTokenStrings)  # Separate tokens by delimiter

    mySock.sendto(msg.encode(), destination)
    print(f"Sent message \"{msg}\" to server at port {destination[1]}")


def broadcastToServers(*msgTokens):
    for addr in serverAddresses:
        sendMessage(msgTokens, addr)


def DEBUG():
    print(f"num of running threads: {threading.active_count()}")
    print(f"leaderElection: {leaderElection}")


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
                broadcastToServers(msg)

        elif len(cmdArgs) == 3:
            if cmd == "send":    # send <msg> <port>
                msg = cmdArgs[1].encode()
                recipient = (socket.gethostname(), int(cmdArgs[2]))

                sendMessage(msg, recipient)


def handleIncomingMsg(msg, addr):
    global leaderElection
    global ballotNum
    global highestB, valWithHighestB, valsAllNone

    print(f"Received message \"{msg}\" from machine at {addr}")

    msgTokens = msg.split('-')

    # Determine whether from client or server
    if addr in serverAddresses:

        # Prepare
        if msgTokens[0] == "prepare":
            bal = eval(msgTokens[1])

            if bal >= ballotNum and bal.depth >= ballotNum.depth:
                ballotNum = bal
                sendMessage(("promise", ballotNum, acceptNum, acceptVal), addr)

        # Promise
        if msgTokens[0] == "promise":
            leaderElection += 1

            balNum = eval(msgTokens[1])
            b = eval(msgTokens[2])
            val = eval(msgTokens[3])

            # Check if all vals are None
            valsAllNone = valsAllNone and (val is None)

            # Eventually, this gets the val with the highest b
            if b > highestB:
                highestB = b
                valWithHighestB = val

    else:
        # Handle client msg
        if msgTokens[0] == "leader":
            ballotNum.seqNum += 1
            threading.Thread(target=sendPrepare, args=(
                ballotNum,), daemon=True).start()


def sendPrepare(ballotNum):
    global valsAllNone, highestB, valWithHighestB, myVal

    # Reset election phase variables
    valsAllNone = True
    highestB = BallotNum(-1, -1, 0)
    valWithHighestB = None

    # Broadcast prepare
    broadcastToServers("prepare", ballotNum)

    # Wait timeout
    time.sleep(5)
    print("Woke up")

    if leaderElection > numServers / 2:
        # Received majority
        print("Received majority")
        print(f"valsAllNone: {valsAllNone}")
        if valsAllNone:
            pass
            # Do nothing, myVal should be set to initial val earlier

        else:
            myVal = valWithHighestB

        # Broadcast accept
        broadcastToServers("accept", ballotNum, myVal)

    else:
        pass


basePort = 8000

# Parse cmdline args
if len(sys.argv) != 2:
    print(f"Usage: python3 {sys.argv[0]} serverID")
    sys.exit()

serverID = int(sys.argv[1])
serverPort = basePort + serverID
leaderElection = 0

# Local variables
ballotNum = BallotNum(0, serverID, 0)
acceptNum = ballotNum
acceptVal = None
myVal = None

# Election phase variables
valsAllNone = True
highestB = BallotNum(-1, -1, 0)

# My socket
mySock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mySock.bind((socket.gethostname(), serverPort))
print("Started server at port", serverPort)

# Addresses of other servers
numServers = 3
serverAddresses = []
for i in range(numServers - 1):
    serverPort = basePort + 1 + ((serverID + i) % numServers)
    serverAddr = (socket.gethostbyname(socket.gethostname()), serverPort)
    # serverSocketOut = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # serverSocketOut.connect( (socket.gethostname(), serverPort) )
    print("Added outgoing server address", serverAddr)
    serverAddresses.append(serverAddr)

threading.Thread(target=handleUserInput, daemon=True).start()

# Poll for incoming messages
while True:
    data, addr = mySock.recvfrom(4096)
    threading.Thread(target=handleIncomingMsg, args=(
        data.decode("ascii"), addr), daemon=True).start()
