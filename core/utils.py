import hashlib
import random
import string
import requests

from .logging import LoggingManager

logger = LoggingManager("Core.Utils")

def get_mc_uuid(username):
    """Get the UUID of a Minecraft account by username"""
    if not username:
        return None
    
    try:
        r = requests.get(f"https://mcprofile.io/api/v1/java/username/{username}")
        r.raise_for_status()
        data = r.json()
        
        return data.get("uuid")
    except requests.RequestException as e:
        logger.error(f"Error fetching UUID for {username}: {e}")
        return None
    
def get_mc_username(uuid):
    """Get the username of a Minecraft account by UUID"""
    if not uuid:
        return None
    
    try:
        r = requests.get(f"https://mcprofile.io/api/v1/java/uuid/{uuid}")
        r.raise_for_status()
        data = r.json()
        
        return data.get("username")
    except requests.RequestException as e:
        logger.error(f"Error fetching username for {uuid}: {e}")
        return None
    
def random_str(length=10):
    """Generate a random string of fixed length"""
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def hash_str(string_to_hash):
    """Hash a string using SHA-256"""
    return hashlib.sha256(string_to_hash.encode()).hexdigest()

def parse_time(num: int):
    #turns seconds into a pretty format, eg:
    #84599 --> 23h 59m 59s
    
    if num <= 0: return "0s"

    out = ""
    if num >= 86400:
        out += f"{int(num // 86400)}d "
        num %= 86400
    
    if num >= 3600:
        out += f"{int(num // 3600)}h "
        num %= 3600
        
    if num >= 60:
        out += f"{int(num // 60)}m "
        num %= 60
        
    if num > 0:
        out += f"{int(num)}s"
        
    return out.strip()