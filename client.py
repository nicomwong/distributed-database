
import socket
import threading
import sys

def handleUserInput():
    while True:
        cmdArgs = input().split()

        cmd = cmdArgs[0]

        if len(cmdArgs) == 3:
            if cmd == "send":    # send <msg> <port>
                msg = cmdArgs[1].encode()
                recipient = (socket.gethostname(), int(cmdArgs[2]) )

                mySock.sendto(msg, recipient)

if len(sys.argv) != 2:
    print(f"Usage: python3 {sys.argv[0]} clientID")
    sys.exit()

basePort = 7000

myID = int(sys.argv[1])
myPort = basePort + myID

mySock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mySock.bind( (socket.gethostname(), myPort) )
print(f"Started client on port {myPort}")

# Start thread to handle user input
threading.Thread(target=handleUserInput, daemon=True).start()

# Poll for incoming messages
# [TODO] Remove later for client probably
while True:
    data, addr = mySock.recvfrom(4096)
    msg = data.decode()
    print(f"Received message \"{msg}\" from machine at {addr}")