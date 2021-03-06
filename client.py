import socket
from datetime import datetime
import threading
import time
import re

# CLIENT KONSTANTER
SERVER = socket.gethostbyname(socket.gethostname())
PORT = 1337
ADDR = (SERVER, PORT)
HEADER = 8
FORMAT = 'utf-8'
DDOS_MESSAGE = "can you handle this?"
LAST_MESSAGE_TIME = datetime.now()
MSG_COUNT = 0
# For at være i stand til at loope i andre tråde
ACTIVE = True

# Default værdier, bliver overskrevet af config-filen
KEEP_ALIVE = False
DDOS_PROTECTION = False
# LÆS CONFIG FOR VALUES
config = open("opt.config", "r")

lines = config.readlines()
for line in lines:
    if line.startswith("KEEP_ALIVE : True"):
        KEEP_ALIVE = True
    if line.startswith("DDOS_PROTECTION : True"):
        DDOS_PROTECTION = True
    if line.startswith("DDOS_AMOUNT"):
        DDOS_AMOUNT = int(line.replace("DDOS_AMOUNT : ", ""))

config.close()

# SOCKET VARIABLE
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def send(msg):
    # Define a new variable and encode it to bytes with given FORMAT constant
    # Ny variabel der for encoded beskeden til bytes ud fra FORMAT konstanten
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)


def receive_msg():
    # Define a variable from the received header, which must be equal (in bytes) to the HEADER constant
    # Decode the received bytestream with the defined FORMAT constant
    msg_length = client.recv(HEADER).decode(FORMAT)
    # Checks not null (if msg_length is not null)
    if msg_length:
        # Set the msg_length variable equal to int typecast of the received (and decoded) bytes.
        msg_length = int(msg_length)
        return client.recv(msg_length).decode(FORMAT)


def listen():
    global ACTIVE, MSG_COUNT
    while ACTIVE:
        try:
            msg = receive_msg()
            if msg == "con-res 0xFE":
                # Protocol response to disconnect
                send("con-res 0xFF")
                client.close()
                ACTIVE = False
                raise ConnectionResetError

            # If the received message count minus the last sent message is not 1, then raise exception
            # I use re.search to look between the two substrings "res-" and "=" for the count
            received_msg_count = int(re.search('res-(.*)=', msg).group(1))
            if received_msg_count - MSG_COUNT != 1 and received_msg_count != 0:
                raise ConnectionResetError

            MSG_COUNT = received_msg_count + 1

        except ConnectionResetError:
            break

        print(msg)
        # Performance trick
        time.sleep(0.1)


def talk():
    global LAST_MESSAGE_TIME, ACTIVE, MSG_COUNT
    while ACTIVE:
        print("[INPUT]:")
        try:
            msg = input()
            send(f"msg-{MSG_COUNT}={msg}")
            LAST_MESSAGE_TIME = datetime.now()
        except OSError:
            print("Connection no longer active")




def heartbeat():
    global LAST_MESSAGE_TIME
    while KEEP_ALIVE:
        # Checks if time since last message is more than 3 seconds
        time_since_last_message = datetime.now() - LAST_MESSAGE_TIME
        if time_since_last_message.total_seconds() > 3:
            try:
                send("con-h 0x00")
                LAST_MESSAGE_TIME = datetime.now()
            except ConnectionResetError:
                print("Lost connection to server")
                break
        # Simply for performance
        time.sleep(0.1)


def ddos_protector():
    while DDOS_PROTECTION:
        send(DDOS_MESSAGE)
        time.sleep(1 / DDOS_AMOUNT)


# Start of Client
def connect_to_server():
    # Client prøver at forbinde til serveren
    # Hvis forsøget mislykkes, venter client 1 sekund og prøver igen
    while True:
        print(f"Attempting to connect to {SERVER} on port {PORT}")
        try:
            client.connect(ADDR)
            print("Connected to server socket")

            # NORMAL CONNECTION
            init_handshake()

            break
        except ConnectionRefusedError:
            print(f"Connection was refused, server may be down or on a different address")
            print("Trying again in 1 sec...")
            time.sleep(1)


# Asks server if the client ip can join
def init_handshake():
    # Handshake step 1
    send("com-0 " + socket.gethostbyname(socket.gethostname()))
    print(f"Sending request to join from [{socket.gethostbyname(socket.gethostname())}]")
    reply_msg = receive_msg()
    print(f"[SERVER] {reply_msg}")
    if reply_msg.startswith("com-0 accept ") and ip_validator(reply_msg.replace("com-0 accept ", "")):
        # Handshake step 3
        send("com-0 accept")
        listen_thread = threading.Thread(target=listen).start()
        heartbeat_thread = threading.Thread(target=heartbeat).start()
        ddos_thread = threading.Thread(target=ddos_protector).start()
        talk()

    else:
        # Handshake step 3
        send("com-0 deny")
        print("Connection denied")
        client.close()


def ip_validator(string):
    try:
        # Checker efter en valid IP adresse
        socket.inet_aton(string)
        return True
    except socket.error:
        return False


connect_to_server()
