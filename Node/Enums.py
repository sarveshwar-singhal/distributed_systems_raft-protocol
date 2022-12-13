from enum import Enum, IntEnum

class RequestType(IntEnum):
    APPEND_RPC = 1
    VOTE_REQUEST = 2
    VOTE_ACK = 3
    APPEND_RPC_RESP = 4,
    STORE = 5,
    RETRIEVE = 6, 
    CONVERT_FOLLOWER = 7,
    TIMEOUT= 8,
    SHUTDOWN = 9,
    LEADER_INFO =10,
    WAKEUP = 11



class NodeState(IntEnum):
    LEADER = 1
    FOLLOWER = 2
    CANDIDATE = 3
    STOPPED = 4
