import json
import socket
import traceback
import time
import os

# Wait following seconds below sending the controller request
# time.sleep(40)

# Read Message Template
msg = json.load(open("Message.json"))

# Initialize
FORMAT = 'utf-8'
sender = "controller"

print("\nEnter CONTROLLER REQUEST")
request = str(input())
print("\nEnter NODE ID\n")
input_target = str(input())
port = 5555
# Request
msg['sender_name'] = sender
# msg['request'] = "SHUTDOWN"#"CONVERT_FOLLOWER"
msg['request'] = request
print(f"\nRequest Created : {msg}")

# Socket Creation and Binding
skt = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
skt.bind((sender, port))

# Send Message
try:
    # Encoding and sending the message
    skt.sendto(json.dumps(msg).encode(FORMAT), (input_target, port))
    if request == "LEADER_INFO":
        msg, addr = skt.recvfrom(1024)
        res = msg.decode('utf-8')
        print(res)
except:
    #  socket.gaierror: [Errno -3] would be thrown if target IP container does not exist or exits, write your listener
    print(f"ERROR WHILE SENDING REQUEST ACROSS : {traceback.format_exc()}")

