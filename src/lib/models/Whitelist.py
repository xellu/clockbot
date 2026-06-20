from enum import Enum

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
        "reapply_in": 60 * 60 * 0.5, #30 mins
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
    "other_1y": {
        "reason": "Other (1 Year)",
        "description": "Please contact a staff member for more information.",
        "reapply_in": 60 * 60 * 24 * 365, #1 year
    },
    "other_inf": {
        "reason": "Other (Inf)",
        "description": "Please contact a staff member for more information.",
        "reapply_in": 60 * 60 * 24 * 365 * 100, #100 years 
    }
}

def WhitelistAnswer():
    return {
        "question": "q",
        "answer": "a" 
    }