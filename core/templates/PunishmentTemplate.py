import uuid
import time

def WarnTemplate():
    return {
        "type": "warn",  # Type of punishment
        
        "id": str(uuid.uuid4()),  # Unique identifier for the warning
        "user": None,  # User ID of the warned user
        "moderator": None,  # Moderator who issued the warning (None if auto-mod)
        
        "reason": None,  # Reason for the warning
        "expires_at": None, # Timestamp of when the warning expires (None if permanent)
        "created_at": time.time(),  # Timestamp of when the warning was created
    }
    
def KickTemplate():
    return {
        "type": "kick",  # Type of punishment
        
        "id": str(uuid.uuid4()),  # Unique identifier for the kick
        "user": None,  # User ID of the kicked user
        "moderator": None,  # Moderator who issued the kick
        
        "reason": None,  # Reason for the kick
        "created_at": time.time(),  # Timestamp of when the kick was created
    }
    
def BanTemplate():
    return {
        "type": "ban",  # Type of punishment
        
        "id": str(uuid.uuid4()),  # Unique identifier for the ban
        "user": None,  # User ID of the banned user
        "moderator": None,  # Moderator who issued the ban
        
        "reason": None,  # Reason for the ban
        "expires_at": None,  # Timestamp of when the ban expires (None if permanent)
        "created_at": time.time(),  # Timestamp of when the ban was created
    }
    