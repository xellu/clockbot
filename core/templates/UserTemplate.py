from enum import Enum
import time
from ..utils import random_str

class WLStatus(Enum):
    INACTIVE = "Inactive"
    PENDING = "Pending"
    REJECTED = "Rejected"
    APPROVED = "Approved"
    
WLDenyReasons = {
    "age": {
        "reason": "Underage",
        "description": "You must be at least 14 years old to play on this server.",
        "reapply_in": 60 * 60 * 24 * 30, #30 days
    },
    "not_english": {
        "reason": "Not english",
        "description": "The server is English only. Please use English in your application.",
        "reapply_in": 60 * 60 * 3, #3 hours
    },
    "no_info": {
        "reason": "Not enough information",
        "description": "Please provide more information in your application.",
        "reapply_in": 60 * 60 * 3, #3 hours
    },
    "nsfw_content": {
        "reason": "Inappropriate content",
        "description": "Your profile or application contains NSFW content.",
        "reapply_in": 60 * 60 * 24 * 7, #7 days
    },
    "other_3h": {
        "reason": "Other (3 Hours)",
        "description": "Please contact a staff member for more information.",
        "reapply_in": 60 * 60 * 3, #3 hours
    },
    "other_1d": {
        "reason": "Other (1 Day)",
        "description": "Please contact a staff member for more information.",
        "reapply_in": 60 * 60 * 24 * 1, #1 day
    },
    "other_7d": {
        "reason": "Other (7 Days)",
        "description": "Please contact a staff member for more information.",
        "reapply_in": 60 * 60 * 24 * 7, #7 days
    },
    "other_30d": {
        "reason": "Other (30 Days)",
        "description": "Please contact a staff member for more information.",
        "reapply_in": 60 * 60 * 24 * 30, #30 days
    },
    "other_inf": {
        "reason": "Other (Inf)",
        "description": "Please contact a staff member for more information.",
        "reapply_in": 60 * 60 * 24 * 365 * 100, #100 years 
    }
}
    
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