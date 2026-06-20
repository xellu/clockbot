import requests
from nautica import Logger
from cachetools import TTLCache, cached

mc_cache_uuid = TTLCache(maxsize=128, ttl=3600)
mc_cache_ign = TTLCache(maxsize=128, ttl=3600)

@cached(cache=mc_cache_uuid)
def get_mc_uuid(username):
    """Get the UUID of a Minecraft account by username"""
    if not username:
        return None
    
    try:
        r = requests.get(f"https://playerdb.co/api/player/minecraft/{username}")
        r.raise_for_status()
        data = r.json()
        
        return data.get("data", {}).get("player", {}).get("id")
    except requests.RequestException as e:
        Logger.error(f"Error fetching UUID for {username}: {e}")
        return None
    
@cached(cache=mc_cache_ign)
def get_mc_username(uuid):
    """Get the username of a Minecraft account by UUID"""
    if not uuid:
        return None
    
    try:
        r = requests.get(f"https://playerdb.co/api/player/minecraft/{uuid}")
        r.raise_for_status()
        data = r.json()
        
        return data.get("data", {}).get("player", {}).get("username")
    except requests.RequestException as e:
        Logger.error(f"Error fetching username for {uuid}: {e}")
        return None
    
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

def escape_md(text):
    """Escape markdown characters in a string"""
    if not text:
        return ""
    
    markdown_chars = ["*", "_", "`", "~", "|", ">", "#", "+", "-", "=", "!", "[", "]", "(", ")", "{", "}", ".", ":"]

    for char in markdown_chars:
        text = text.replace(char, f"\\{char}")
    
    return text