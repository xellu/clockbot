import time

from nautica import Services, Config

from plugins.Clockwork import Clockwork
from src.lib.Util import get_mc_username, get_mc_uuid
from src.lib.Mongo import Mongo
from src.lib.models.User import UserTemplate
from src.lib.models.Whitelist import WLStatus
from src.lib.Clockwork import CW as CWCore


class UserActionResponse:
    def __init__(self, ok: bool, error: str | None = None, meta: any = None):
        self.ok = ok
        self.error = error
        self.meta = meta


class UserManager:
    def __init__(self, discord = None, minecraft = None):
        """
        A class to manage user accounts.
        
        Parameters:
            discord (int): Discord ID of the user.
            minecraft (str): Minecraft UUID of the user.
        
        Raises:
            ValueError: If neither discord nor minecraft is provided.
        """
        
        self.discord = discord
        self.minecraft = minecraft
        
        self.user = None
        
        if not discord and not minecraft:
            raise ValueError("Discord ID or Minecraft UUID must be provided")
        
        self.load()
        
    def is_valid(self):
        """Check if the user is valid."""
        return self.user is not None
    
    def load(self):
        if self.discord:
            self.user = Mongo("users").find_one({"discord": self.discord})
        elif self.minecraft:
            self.user = Mongo("users").find_one({"minecraft": self.minecraft})
    
        if self.user:
            self.discord = self.user["discord"]
            self.minecraft = self.user["minecraft"]
    
    def update(self):
        """Update the user in the database."""
        if not self.is_valid():
            return UserActionResponse(False, "User not found")
        
        Mongo("users").update_one({"discord": self.discord}, {"$set": self.user})
        
        return UserActionResponse(True)
    
    def get(self, key: str|None = None):
        return self.user if key is None else self.user.get(key)
        
    def link(self, minecraft):
        """Link a Minecraft account to the user."""
        if not self.is_valid():
            return UserActionResponse(False, "User not found")
        
        if self.user["minecraft"]:
            return UserActionResponse(False, "User already has a linked Minecraft account")
        
        uuid = get_mc_uuid(minecraft)
        if not uuid:
            return UserActionResponse(False, "Invalid Minecraft username")
        
        if self.user["whitelist"]["status"] == WLStatus.APPROVED.value:
            #Puffer.execute_command(f"/whitelist add {minecraft}")
            CWCore.WhitelistAdd(uuid)
        
        self.user["minecraft"] = uuid
        self.user["whitelist"]["status"] = WLStatus.APPROVED.value
        self.update()
        
        return UserActionResponse(True)
    
    def unlink(self):
        """Unlink the Minecraft account from the user."""
        if not self.is_valid():
            return UserActionResponse(False, "User not found")
        
        username = get_mc_username(self.user["minecraft"])
        if self.user["whitelist"]["status"] == WLStatus.APPROVED.value and username:
            # Puffer.execute_command(f"/whitelist remove {username}")
            CWCore.WhitelistRemove(self.user["minecraft"])
        
        self.user["minecraft"] = None
        self.update()
        
        return UserActionResponse(True)
    
    def relink(self, minecraft):
        """Switches the Minecraft account linked to the user."""
        if not self.is_valid():
            return UserActionResponse(False, "User not found")
        
        if not self.user["minecraft"]:
            return UserActionResponse(False, "User does not have a linked Minecraft account")
        
        status = self.unlink()
        if not status.ok:
            return status
        
        return self.link(minecraft)
    
    def delete(self):
        """Delete the user."""
        if not self.is_valid():
            return UserActionResponse(False, "User not found")
        
        if self.user["whitelist"]["status"] == WLStatus.APPROVED.value and self.user["minecraft"]:
            # Puffer.execute_command(f"/whitelist remove {get_mc_username(self.user['minecraft'])}")
            CWCore.WhitelistRemove(self.user["minecraft"])
            
        Mongo("users").delete_one({"discord": self.discord})
        self.user = None
        
        return UserActionResponse(True)
    
    def create(self, discord = None, minecraft = None):
        """Create a new user."""
        if self.is_valid():
            return UserActionResponse(False, "User already exists")
        
        uuid = get_mc_uuid(minecraft)
        if not uuid:
            return UserActionResponse(False, "Invalid Minecraft username")
        
        if self.discord is None and discord is None:
            return UserActionResponse(False, "Discord ID must be provided")
        
        if self.minecraft is None and minecraft is None:
            return UserActionResponse(False, "Minecraft username must be provided")
        
        if self.discord is None:
            self.discord = discord
            
        if self.minecraft is None:
            self.minecraft = minecraft
        
        self.user = UserTemplate()
        self.user["discord"] = self.discord
        self.user["minecraft"] = uuid
        
        self.user["whitelist"]["status"] = WLStatus.INACTIVE.value
        
        Mongo("users").insert_one(self.user)
        self.load()
        
        return UserActionResponse(True)
    
    def create_unlinked(self, discord = None):
        """Create a new user without linking a Minecraft account."""
        if self.is_valid():
            return UserActionResponse(False, "User already exists")
        
        if self.discord is None and discord is None:
            return UserActionResponse(False, "Discord ID must be provided")
        
        if self.discord is None:
            self.discord = discord
            
        self.user = UserTemplate()
        self.user["discord"] = self.discord
        
        self.user["whitelist"]["status"] = WLStatus.INACTIVE.value
        
        Mongo("users").insert_one(self.user)
        self.load()
        
        return UserActionResponse(True)
    
    def just_seen(self):
        """Update the last seen timestamp of the user."""
        if not self.is_valid():
            return UserActionResponse(False, "User not found")
        
        self.user["last_seen"] = time.time()
        self.update()
        
        return UserActionResponse(True)
    
    def get_seen(self, md: bool = False):
        """"
        Get the last seen timestamp of the user.
        params:
            md (bool): If True, will return as markdown string.
        
        returns:
            str: Last seen timestamp as a string. (if md is True)
            int: Last seen timestamp as an int. (-1 = Never, -2 = Online, *= Timestamp)
        """
        
        if not self.is_valid():
            return UserActionResponse(False, "User not found")
        
        if not md:
            if CWCore.logged_in:
                for player in CWCore.status["online"]["list"]:
                    if player["uuid"] == self.user["minecraft"]:
                        return UserActionResponse(True, meta=-2)
                    
            return UserActionResponse(True, meta=self.user["last_seen"] or -1)
        
        if CWCore.logged_in:
            for player in CWCore.status["online"]["list"]:
                if player["uuid"] == self.user["minecraft"]:
                    return UserActionResponse(True, meta="Online")
        
        if self.user["last_seen"]:
            return UserActionResponse(True, meta=f"<t:{int(self.user['last_seen'])}:R> <t:{int(self.user['last_seen'])}:f>")
        return UserActionResponse(True, meta="Never")
    
    def whitelist_approve(self, moderator: int):
        """Approve the user for whitelisting."""
        if not self.is_valid():
            return UserActionResponse(False, "User not found")
        
        if self.user["whitelist"]["status"] == WLStatus.APPROVED.value:
            return UserActionResponse(False, "User already approved")
        
        self.user["whitelist"]["status"] = WLStatus.APPROVED.value
        self.user["whitelist"]["moderator"] = moderator
        self.user["whitelist"]["reason"] = None
        self.user["whitelist"]["reapply_in"] = None
        self.update()
        
        # Puffer.execute_command(f"/whitelist add {get_mc_username(self.user['minecraft'])}")
        CWCore.WhitelistAdd(self.user["minecraft"])
        
        return UserActionResponse(True)
    
    def whitelist_reject(self, moderator: int, reason: str = None, reapply_in: int = 0):
        """Reject the user for whitelisting."""
        if not self.is_valid():
            return UserActionResponse(False, "User not found")
        
        if self.user["whitelist"]["status"] == WLStatus.REJECTED.value:
            return UserActionResponse(False, "User already rejected")
        
        self.user["whitelist"]["status"] = WLStatus.REJECTED.value
        self.user["whitelist"]["moderator"] = moderator
        self.user["whitelist"]["reason"] = reason
        self.user["whitelist"]["reapply_in"] = time.time() + reapply_in
        self.update()
        
        # Puffer.execute_command(f"/whitelist remove {get_mc_username(self.user['minecraft'])}")
        CWCore.WhitelistRemove(self.user["minecraft"])
        
        return UserActionResponse(True)
    
    def whitelist_remove(self, moderator: int):
        """Remove the user from the whitelist."""
        if not self.is_valid():
            return UserActionResponse(False, "User not found")
        
        self.user["whitelist"]["status"] = WLStatus.INACTIVE.value
        self.user["whitelist"]["moderator"] = moderator
        self.user["whitelist"]["reason"] = None
        self.user["whitelist"]["reapply_in"] = None
        self.update()
        
        # Puffer.execute_command(f"/whitelist remove {get_mc_username(self.user['minecraft'])}")
        CWCore.WhitelistAdd(self.user["minecraft"])
        
        return UserActionResponse(True)