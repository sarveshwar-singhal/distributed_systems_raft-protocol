
import json
from logging import exception
from sre_constants import SUCCESS


class BaseMessage:
    def __init__(self,sender_name,request,term) -> None:
        self.sender_name = sender_name
        self.request = request
        self.term = term
        #add properties according to request type
            
            

class AppendRPCMessage(BaseMessage):
    def __init__(self, sender_name, request, term,leader_id,leader_commit = -1 ,prevLogIndex=-1,prevLogTerm = -1, logs = []) -> None:
        super().__init__(sender_name, request, term)
        self.leader_id = leader_id
        self.term = term
        self.logs = logs
        #Currently -1, for phase 3
        self.prevLogIndex = prevLogIndex
        #Currently -1, for phase 3
        self.prevLogTerm = prevLogTerm
        self.leader_commit = leader_commit

#NO APPEND ENTRIES RESPONSE _ CLASS TO BE ADDED FOR LATER
class AppendRPCRespMessage(BaseMessage):
    def __init__(self, sender_name, request, term,success= False,next_index = -1) -> None:
        super().__init__(sender_name, request, term)
        self.success = success
        self.next_index = next_index


class RequestVoteMessage(BaseMessage):
    def __init__(self, sender_name, request, term,candidate_id,lastLogIndex=-1,lastLogTerm=-1) -> None:
        super().__init__(sender_name, request, term)
        self.candidate_id = candidate_id
        #Currently -1, for phase 3
        self.lastLogIndex = lastLogIndex
        #Currently -1, for phase 3
        self.lastLogTerm = lastLogTerm

class RequestVoteResponse(BaseMessage):
    def __init__(self, sender_name, request, term,vote_granted) -> None:
        super().__init__(sender_name, request, term)
        self.vote_granted = vote_granted





