
import socket
import sys
import threading


basePort = 8000

# Parse cmdline args
if len(sys.argv) != 2:
    print(f"Usage: python3 {sys.argv[0]} serverID")
    sys.exit()

serverID = int(sys.argv[1])
serverPort = basePort + serverID

currServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
currServer.bind((socket.gethostname(), serverPort))
print(f"server listening on {(socket.gethostname(), serverPort)}")

# Print initialization
print("Started server on port", serverPort)

# .sendto() .recvfrom()
numServers = 3
serverAddressesOut = []
for i in range(numServers - 1):
    serverPort = basePort + 1 + ((serverID + i) % numServers)
    serverAddr = (socket.gethostname(), serverPort)
    # serverSocketOut = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # serverSocketOut.connect( (socket.gethostname(), serverPort) )
    print("Added outgoing server address", serverAddr)
    serverAddressesOut.append(serverAddr)


def broadcastTest():
    testMessage = f"test message from serverID {serverID}"

    for server in serverAddressesOut:
        currServer.sendto(testMessage.encode("ascii"), server)
        print(f"sent test message to server operating on port {server[1]}")
        # threading.Thread(target=handleIncoming, args=(
        #     server,), daemon=True).start()


def handleIncoming(message, addr):
    print(f"Server accepted message from another server on port {addr[1]}")
    print(f"message: {message}")


def DEBUG():
    print(f"num of running threads: {threading.active_count()}")


def handleUserInput():
    while True:
        command = input()

        if (command == "connect"):
            broadcastTest()

        if (command == "DEBUG"):
            DEBUG()


threading.Thread(target=handleUserInput, daemon=True).start()

while True:
    data, addr = currServer.recvfrom(4096)
    threading.Thread(target=handleIncoming, args=(
        data.decode("ascii"), addr), daemon=True).start()
