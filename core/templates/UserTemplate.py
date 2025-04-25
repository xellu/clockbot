from enum import Enum

class WLStatus(Enum):
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
        }
    }