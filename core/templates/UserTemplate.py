from enum import Enum
import time
from ..utils import random_str

class WLStatus(Enum):
    INACTIVE = "Inactive"
    PENDING = "Pending"
    REJECTED = "Rejected"
    APPROVED = "Approved"
    
WLKeyNames = {
    "age": "Age",
    "region": "Region",
    "howFound": "How did you find us?",
    "whyJoin": "What interests you about the server?",
    "playedSMPs": "Have you played on any other SMPs?",
    "playedCreate": "Have you played with Create Mod before?",
    "goodAt": "What are you good at?",
    "joinTown": "Do you want to be a part of any town?",
    "friendsPlaying": "Do you have any friends playing on the server?",
    "note": "Anything else you want to add?",
}

def UserTemplate():
    return {
        "discord": 0, #Discord ID
        "minecraft": "", #Minecraft UUID
        
        "last_seen": None, #Last seen timestamp
        
        "whitelist": {
            "status": WLStatus.PENDING.value, #Whitelist status
            "moderator": None, #Moderator who approved/rejected the whitelist (their Discord ID)
            "reapply_in": None, #timestamp of when the user can reapply for whitelist (only if rejected)
            "reason": None, #Reason for rejection
            "answers": {} #Whitelist apply answers
        },
        
        "created_at": time.time(), #timestamp of when the user was created
    }
    
def ActionTemplate():
    return {
        "id": f"GNRC-{random_str(8)}",
        "type": "action", #action type (e.g. "wl-add", "wl-remove")
        "msg": 0, #message id
        
        "user": 0, #user id
        "reason": None, #reason for the action
    }