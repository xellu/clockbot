import time
from .Whitelist import WLStatus

def UserTemplate():
    return {
        "discord": 0, #Discord ID
        "minecraft": "", #Minecraft UUID
        
        "last_seen": None, #Last seen timestamp
        "isAdmin": False,
        
        "whitelist": {
            "status": WLStatus.INACTIVE.value, #Whitelist status
            "moderator": None, #Moderator who approved/rejected the whitelist (their Discord ID)
            "reapply_in": None, #timestamp of when the user can reapply for whitelist (only if rejected)
            "reason": None, #Reason for rejection
            "answers": [] #Whitelist apply answers
        },
        
        "created_at": time.time(), #timestamp of when the user was created
    }