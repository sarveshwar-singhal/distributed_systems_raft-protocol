from base64 import decode
from datetime import datetime, timedelta
from genericpath import exists
from logging import exception
from random import randint, random
import time
import json
import socket
import concurrent.futures
import threading
import traceback
from urllib import request
from Enums import RequestType, NodeState
from Message import AppendRPCMessage, RequestVoteMessage, RequestVoteResponse, AppendRPCRespMessage


class RaftServer:
    
    def __init__(self, node_name, members, election_timeout_range, heartbeat_timeout) -> None:
        # self.outfile = open('/usr/json_data.json', 'a')
        self.currentTerm = 0
        self.leader_id = ""
        self.shutdown = False
        self.votedFor = ""
        self.votes_granted = []

        self.node_name = node_name
        self.node_state = NodeState.FOLLOWER
        print(f"\n\n\n\n\n memberrrr::: {members} \n\n\n\n\n")
        self.initialize_socket()

        self.election_timeout = self.get_election_timeout(election_timeout_range)
        self.election_timer = datetime.now()  # time.time()

        self.heartbeat_timeout = heartbeat_timeout
        self.heartbeat_timer = datetime.now()  # time.time()

        self.timeout_loop_thread = threading.Thread(target=self.timeout_looper)

        self.socket_listener_thread = threading.Thread(target=self.socket_listener)

        self.members = members
        self.timeout_range = election_timeout_range

        #Log related
        self.logs = [[0,0,"",""]] #index,term
        #Initialize nextIndex array to length of the members
        self.next_index = dict()
        self.match_index = dict()
        # for member in self.members:
        #     self.next_index[member] = 1

        self.commit_index = 0
        
        #End

        #Load logs and update the values
        self.load_stored_logs()

        self.timeout_loop_thread.start()
        self.socket_listener_thread.start()

    def load_stored_logs(self):
        if exists('/usr/json_data.json'):
            print("\nFIle Exists")
            f1 = open('/usr/json_data.json', 'r')
            # data = f1.read()
            s_data = json.load(f1)
            # last_log = s_data[-1]
            self.currentTerm = s_data['currentTerm']
            self.votedFor = s_data['votedFor']
            # print(s_data)
            for log in s_data['log']:
                self.logs.append(log)
            
            print("\n\n\n\n\n LOADED LOGS \n\n\n",self.logs,"\n",self.currentTerm,"\n",self.votedFor,"\n\n\n####")

    def get_election_timeout(self, timeout_range):
        return randint(int(timeout_range[0]), int(timeout_range[1]))

    def timeout_looper(self):

        while True:
            if self.shutdown:
                return

            if self.node_state == NodeState.LEADER:
                if datetime.now() >= self.heartbeat_timer + timedelta(milliseconds=self.heartbeat_timeout):
                    self.send_heartbeat()
                    print(
                        f"Heartbeat call :: {self.node_name} :: Current term {self.currentTerm} :: Current State {str(self.node_state)} :: LOGS: \n {self.logs}\n")
            elif datetime.now() >= self.election_timer + timedelta(milliseconds=self.election_timeout):
                # change state from follower to candidate
                self.become_candidate()
                print(f"Current term {self.currentTerm} :: Current State {str(self.node_state)}")

    def socket_listener(self):
        while True:
            try:
                msg, addr = self.socket.recvfrom(1024)
            except:
                print(f"NO DATA TO READ .......................")
            
            if not msg:
                continue
            
            # Decoding the Message received from nodes
            decoded_msg = json.loads(msg.decode('utf-8'))
            requestType = RequestType[decoded_msg['request']]
           #phase_4 controller
            if requestType == RequestType.STORE:
                self.perform_store_op(addr, decoded_msg)
            elif requestType == RequestType.RETRIEVE:
                self.perform_retrieve_op(addr)
            elif requestType == RequestType.CONVERT_FOLLOWER:
                self.convert_to_follower()
            elif requestType == RequestType.TIMEOUT:
                self.become_candidate()
            elif requestType == RequestType.SHUTDOWN:
                self.shutdown = True
                return
            elif requestType == RequestType.LEADER_INFO:
                self.socket.sendto(json.dumps({"LEADER":self.leader_id}).encode('utf-8'), ("controller", 5555))
            elif requestType == RequestType.VOTE_REQUEST:
                self.handle_vote_request(decoded_msg)
            elif requestType == RequestType.APPEND_RPC:
                self.handle_append_rpc(decoded_msg)
            elif requestType == RequestType.VOTE_ACK:
                self.handle_vote_request_response(decoded_msg)
                self.check_majority_votes()
            elif requestType == RequestType.APPEND_RPC_RESP:
                self.handle_append_rpc_response(decoded_msg)

    def perform_retrieve_op(self, addr):
        print(self.node_state)
        if self.node_state == NodeState.LEADER:
                    #return data
            try:
                m_logs = [{"Term":l[1],"Key":l[2],"Value":l[3]} for l in self.logs]
                data = {"sender_name":self.node_name,"term":self.currentTerm,"request":"RETRIEVE","key":"COMMITED_LOGS","value":m_logs}
                self.socket.sendto(json.dumps(data).encode('utf-8'), addr)
                
            except:
                print("error in retrieve request")
        else:
                    # return leader info
            info = {}
            info['sender_name'] = self.node_name
            info['term'] = self.currentTerm
            info['request'] = 'LEADER_INFO'
            info['key'] = 'LEADER'
            info['value'] = str(self.leader_id)
            self.socket.sendto(json.dumps(info).encode('utf-8'), addr)

    def perform_store_op(self, addr, decoded_msg):
        #storing data in nodes
        if self.node_state == NodeState.LEADER:
                    #insert data to persist
            self.logs.append([len(self.logs),self.currentTerm,decoded_msg["key"],decoded_msg["value"]])
            self.add_log_entry_to_file([len(self.logs),self.currentTerm,decoded_msg["key"],decoded_msg["value"]])
            self.socket.sendto(json.dumps({"request":"SUCCESS"}).encode('utf-8'), addr)
        else:
                    # return leader info
            info = {}
            info['sender_name'] = self.node_name
            info['term'] = None
            info['request'] = 'LEADER_INFO'
            info['key'] = 'LEADER'
            info['value'] = str(self.leader_id)
            print("output here")
            print(addr, type(addr))
            self.socket.sendto(json.dumps(info).encode('utf-8'), addr)

    def become_candidate(self):
        self.node_state = NodeState.CANDIDATE
        self.reset_election_timer()
        # increase the term
        self.currentTerm += 1
        self.votedFor = self.node_name
        self.votes_granted = [] 
        self.votes_granted.append(self.node_name)

        # Get the votes for each member

        for member in self.members:
            # request vote
            index, term, _, _ = self.logs[-1]
            messageObj = RequestVoteMessage(self.node_name, RequestType.VOTE_REQUEST.name, self.currentTerm, self.node_name,index,term)
            msg_bytes = json.dumps(messageObj.__dict__).encode()
            print(f"VOTE REQUEST :: SENDING TO :: {member}")
            try:
                self.socket.sendto(msg_bytes, (member, 5555))
            except:
                if member in self.members:
                    self.members.remove(member)
                print(f"VOTE REQUEST ERROR:: \" {member}\" :: Not available")
                continue

        self.check_majority_votes()

    def become_leader(self):
        self.node_state = NodeState.LEADER
        #self.reset_heartbeat_timer()
        self.next_index = dict()
        self.match_index = dict()
        for member in self.members:
            self.next_index[member] = len(self.logs)
            self.match_index[member] = 0

        
        # send each node update about becoming leader
        # send appendentries
        self.send_append_entry()

    def send_heartbeat(self):
        self.reset_heartbeat_timer()
        # send append entries request
        self.send_append_entry()

    def send_append_entry(self):
        for member in self.members:
            if member not in self.next_index:
                continue
            index, term,_,_ = self.logs[self.next_index[member]-1]
            logs = self.logs[self.next_index[member]:]
            messageObj = AppendRPCMessage(self.node_name, RequestType.APPEND_RPC.name, self.currentTerm, self.node_name,prevLogIndex=index,\
                prevLogTerm=term,logs=logs,leader_commit=self.commit_index)
            msg_bytes = json.dumps(messageObj.__dict__).encode()
            try:
                self.socket.sendto(msg_bytes, (member, 5555))
            except:
                if member in self.members:
                    self.members.remove(member)
                print(f"send_append_entry ERROR:: Node -> {member} :: Not available")
                continue

    def initialize_socket(self):
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        # Bind the node to sender ip and port
        self.socket.bind((self.node_name, 5555))

    def handle_vote_request(self, msg):
        # obj = json.loads(msg)
        requestObj = RequestVoteMessage(**msg)
        
        if requestObj.sender_name.lower() not in self.members and requestObj.sender_name.lower() != self.node_name.lower():
            self.members.append(requestObj.sender_name.lower())
            print(f"\n######## members :: {self.members}")

        # parse the message
        self.set_election_term(requestObj.term)
        
        last_log = self.logs[-1]
        is_last_valid = requestObj.lastLogTerm > last_log[1] or (requestObj.lastLogTerm == last_log[1] and requestObj.lastLogIndex >= last_log[0]) 

        # Check if node term is less than or greater than received term
        granted = (self.currentTerm == requestObj.term) and is_last_valid and (self.votedFor == requestObj.candidate_id or self.votedFor == "") 

        print(f"self.currentTerm < requestObj.term :: {self.currentTerm} < {requestObj.term}")

        if granted:  # request granted
            self.votedFor = requestObj.candidate_id

        messageObj = RequestVoteResponse(requestObj.sender_name.lower(), RequestType.VOTE_ACK.name, self.currentTerm, granted)
        msg_bytes = json.dumps(messageObj.__dict__).encode()
        self.socket.sendto(msg_bytes, (requestObj.sender_name.lower(), 5555))

        # SEND:-> voting request response as granted

    def handle_vote_request_response(self, msg):
        # obj = json.loads(msg)
        print("TESTTSDSDT :: ", msg)
        requestObj = RequestVoteResponse(**msg)

        # check term is up to date or not
        if requestObj.term <= self.currentTerm and requestObj.vote_granted:
            self.currentTerm = requestObj.term
            self.votes_granted.append(requestObj.sender_name.lower())
            self.check_majority_votes()

    def handle_append_rpc(self, msg):

        ##obj = json.loads(msg)
        requestObj = AppendRPCMessage(**msg)

        # if candidate, fall back to follower state
        # update term
        # reset election timer
        if self.node_state == NodeState.CANDIDATE:
            self.convert_to_follower()
        
        self.leader_id = requestObj.leader_id.lower()


        self.set_election_term(requestObj.term)
        self.reset_election_timer()

        is_log_valid = requestObj.prevLogIndex < len(self.logs) and self.logs[requestObj.prevLogIndex][1] == requestObj.prevLogTerm
        messageObj = None
        if self.currentTerm == requestObj.term and is_log_valid:
            self.update_logs(requestObj.logs)
            if requestObj.leader_commit > self.commit_index:
                self.commit_index = min(requestObj.leader_commit,self.logs[-1][0]) if  len(requestObj.logs) > 0 else requestObj.leader_commit
        
            messageObj = AppendRPCRespMessage(self.node_name, RequestType.APPEND_RPC_RESP.name, self.currentTerm,success=True,\
                next_index=requestObj.prevLogIndex+len(requestObj.logs)+1)
        else:
            messageObj = AppendRPCRespMessage(self.node_name,RequestType.APPEND_RPC_RESP.name,self.currentTerm,success=False,next_index=len(self.logs))
        
        msg_bytes = json.dumps(messageObj.__dict__).encode()
        self.socket.sendto(msg_bytes, (requestObj.sender_name.lower(), 5555))

        # NO Response for PHASE-3
        # send response for appendentries with log commit ids
    def handle_append_rpc_response(self,msg):
        requestObj = AppendRPCRespMessage(**msg)

        if requestObj.term <= self.currentTerm:
            if requestObj.success:
                self.next_index[requestObj.sender_name.lower()] = requestObj.next_index
                self.match_index[requestObj.sender_name.lower()] = requestObj.next_index -1 
                self.increase_commit_index()
            else:
                self.next_index[requestObj.sender_name.lower()] = min(requestObj.next_index,self.next_index[requestObj.sender_name.lower()]-1)

    
    def update_logs(self, logs):
        for index, term,key,value in logs:
            if index < len(self.logs):
                if self.logs[index][1] != term:
                    self.logs.append([index,term,key,value])
                    self.add_log_entry_to_file([index,term,key,value])
            else:
                self.logs.append([index,term,key,value])
                self.add_log_entry_to_file([index,term,key,value])
    
    def add_log_entry_to_file(self,logentry):
        data_to_store = {"currentTerm" : self.currentTerm, "votedFor":self.votedFor, "log" : self.logs,
        "timeout_interval":self.election_timeout,"heartbeat_interval":self.heartbeat_timeout}
        with open('/usr/json_data.json', "w") as f:
            json.dump(data_to_store,f)
        # data_to_store = json.dumps(data_to_store)
        # json.dump(data_to_store, self.outfile)


    def convert_to_follower(self):
        self.node_state = NodeState.FOLLOWER
        self.reset_election_timer()

    def check_majority_votes(self):
        if self.node_state == NodeState.CANDIDATE \
                and len(self.votes_granted) > (
                (len(self.members)) // 2):  
            self.become_leader()

    def set_election_term(self, newTerm):
        if self.currentTerm >= newTerm:
            return

        self.currentTerm = newTerm
        self.votedFor = ""
        self.convert_to_follower()

    def reset_election_timer(self):
        self.election_timer = datetime.now()  # time.time()
        self.election_timeout = self.get_election_timeout(self.timeout_range)

    def reset_heartbeat_timer(self):
        self.heartbeat_timer = datetime.now()  # time.time()

    def increase_commit_index(self):
        node_vals = list(self.match_index.values())
        # print("\n\n\n\n\node_vals\n\n\n\n\n",node_vals,type(node_vals))
        node_vals.sort()
        self.commit_index = max(self.commit_index,node_vals[len(node_vals)//2])

