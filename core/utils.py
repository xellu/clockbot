import hashlib
import random
import string
import requests

from .logging import LoggingManager

logger = LoggingManager("Core.Utils")

def get_mc_uuid(username):
    """Get the UUID of a Minecraft account by username"""
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