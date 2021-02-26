
import socket
import threading
import sys
import threading


def broadcastToServers(msg):
    for addr in serverAddresses:
        mySock.sendto(msg.encode("ascii"), addr)
        print(f"Sent message \"{msg}\" to server at port {addr[1]}")


def DEBUG():
    print(f"num of running threads: {threading.active_count()}")


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

                mySock.sendto(msg, recipient)


def handleIncomingMsg(msg, addr):
    print(f"Received message \"{msg}\" from machine at {addr}")

    # Determine whether from client or server
    if addr in serverAddresses:
        # Handle server msg
        pass

    else:
        # Handle client msg
        pass


basePort = 8000

# Parse cmdline args
if len(sys.argv) != 2:
    print(f"Usage: python3 {sys.argv[0]} serverID")
    sys.exit()

serverID = int(sys.argv[1])
serverPort = basePort + serverID

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
