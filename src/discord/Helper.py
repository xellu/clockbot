from src.lib.User import UserManager
from src.lib.Discord import Bot

import discord
from nautica import Config

async def isStaff(user: UserManager) -> bool:
    server: discord.Guild = await Bot.fetch_guild(Config("clockbot")["servers.discord"])
    if not server: return False
    
    member: discord.Member = server.fetch_member(user.get("discord"))
    if not member: return False
    
    roles = [r.id for r in member.roles]
    for roleId in Config("clockbot")["staff.admins"] + Config("clockbot")["staff.mods"]:
        if roleId in roles: return True
        
    return False

async def isAdmin(user: UserManager) -> bool:
    server: discord.Guild = await Bot.fetch_guild(Config("clockbot")["servers.discord"])
    if not server: return False
    
    member: discord.Member = server.fetch_member(user.get("discord"))
    if not member: return False
    
    roles = [r.id for r in member.roles]
    for roleId in Config("clockbot")["staff.admins"]:
        if roleId in roles: return True
        
    return False

