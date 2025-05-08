from enum import Enum
import time
from ..utils import random_str

class WLStatus(Enum):
    INACTIVE = "Inactive"
    PENDING = "Pending"
    REJECTED = "Rejected"
    APPROVED = "Approved"

def UserTemplate():
    return {
        "discord": 0, #Discord ID
        "minecraft": "", #Minecraft UUID
        
        "last_seen": None, #Last seen timestamp
        
        "whitelist": {
            "status": WLStatus.PENDING.value, #Whitelist status
            "moderator": None, #Moderator who approved/rejected the whitelist (their Discord ID)
            "reapply_in": None, #timestamp of when the user can reapply for whitelist (only if rejected)
            "reason": None #Reason for rejection
        },
        
        "created_at": time.time(), #timestamp of when the user was created
    }
    
def ApplicationTemplate(): 
    return {
        "user": 0,
        
        "index": 0, #question index
        "channel": 0, #channel id where the application was sent
        
        "answers": {
            #"question_id": answer,
            #...
        },
        
        "created_at": time.time(), #timestamp of when the application was created
    }
    
def ActionTemplate():
    return {
        "id": f"GNRC-{random_str(8)}",
        "type": "action", #action type (e.g. "wl-add", "wl-remove")
        "msg": 0, #message id
        
        "user": 0, #user id
        "reason": None, #reason for the action
    }