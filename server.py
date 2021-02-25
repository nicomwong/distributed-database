
import socket
import sys


basePort = 8000

# Parse cmdline args
if len(sys.argv) != 2:
    print(f"Usage: python3 {sys.argv[0]} serverID")
    sys.exit()

serverID = int(sys.argv[1])
serverPort = basePort + serverID

# Print initialization
print("Started server on port", serverPort)

numServers = 3
serverAddressesOut = []
for i in range(numServers - 1):
    serverPort = basePort + 1 + ( (serverID + i) % numServers)
    serverAddr = (socket.gethostname(), serverPort)
    # serverSocketOut = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # serverSocketOut.connect( (socket.gethostname(), serverPort) )
    print("Added outgoing server address", serverAddr)
    serverAddressesOut.append(serverAddr)
