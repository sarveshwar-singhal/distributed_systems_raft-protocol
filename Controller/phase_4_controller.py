import socket
import threading
import json

FORMAT = 'utf-8'
PORT = 5555
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

skt = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
skt.bind(ADDR)

# conn.recvfrom(1024)

REQ = {}
REQ['sender_name'] = 'Controller'
REQ['term'] = None
REQ['request'] = None
REQ['key'] = None
REQ['value'] = None


# def handle_store()


def main():
    while True:
        op = input("STORE, RETRIEVE, TERMINATE\n")
        if op == 'TERMINATE':
            break
        if op == 'STORE':
            input_target = str(input("Target Node: "))
            key = str(input("Enter key: "))
            value = str(input("Enter value: "))
            req = REQ
            req['request'] = 'STORE'
            req['key'] = key
            req['value'] = value
            while True:
                skt.sendto(json.dumps(req).encode(FORMAT), (input_target, PORT))
                msg, addr = skt.recvfrom(2048)
                res = json.loads(msg.decode(FORMAT))
                print(res)
                if res['request'] == 'SUCCESS':
                    break
                else:
                    input_target = res['value']
        if op == 'RETRIEVE':
            input_target = str(input("Target Node: "))
            req = REQ
            req['request'] = 'RETRIEVE'
            while True:
                skt.sendto(json.dumps(req).encode(FORMAT), (input_target, PORT))
                msg, addr = skt.recvfrom(2048)
                res = json.loads(msg.decode(FORMAT))
                if res['request'] == 'RETRIEVE':
                    print(res)
                    break
                elif res['request'] == 'LEADER_INFO':
                    print(res)
                    print("Retrieveing leader information ....")
                    input_target = res['value']

            #server.sendto(req)

if __name__ == "__main__":
    main()
