import json
from logging import exception
import asyncio
import os
import socket

from server import RaftServer

if __name__ == "__main__":
    hostname = os.getenv("node_name")
    print(f"starting node :: {hostname}")
   
    members = os.getenv('MEMBERS')
    memList =[]
    
    for mem in members.split(","):
        if hostname.lower() == mem.lower():
            continue
        memList.append(mem)

    election_timeout_range =os.getenv('ELECTION_TIMEOUT_RANGE_MS').split(",")
    heartbeat_timeout = int(os.getenv('HEARTBEAT_TIMEOUT_MS'))
    
    server = RaftServer(hostname,memList,election_timeout_range,heartbeat_timeout)
    
    server.socket_listener_thread.join()
    server.timeout_loop_thread.join()

    print("Finished")