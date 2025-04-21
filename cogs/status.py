from discord.ext import commands, tasks
from discord import app_commands

from mdbb import Bot, Config
import requests
import enum

class State(enum.Enum):
    NETWORK_ERROR = -1
    OFFLINE = 0
    ONLINE = 1
    MAINTENANCE = 2

class Status(commands.Cog):
    def __init__(self):
        self.bot = Bot
    
    @tasks.loop(seconds=60)
    async def update_status(self):
        r = requests.get(f"https://api.mcstatus.io/v2/status/java/{Config.get('STATUS.TARGET.IP')}")
        if r.status_code != 200:
            self.set_channel_status(State.NETWORK_ERROR)
            return
        
        data = r.json()
        if data["online"]:
            self.set_channel_status(State.ONLINE, data["players"]["online"])
            return
        
        #TODO: make maintenance work
        self.set_channel_status(State.OFFLINE)
        
            
    async def set_channel_status(self, state, players = None):
        channel = await self.bot.fetch_channel(Config.get("STATUS.CHANNEL"))
        
        match state:
            case State.ONLINE:
                await channel.edit(name=f"{'🔥' if players > 15 else '✅'} {players} Online")
            case State.OFFLINE:
                await channel.edit(name=f"⛔ Server Offline")
            case State.MAINTENANCE:
                await channel.edit(name=f"⚠️ {Config.get('STATUS.NAME')} | Maintenance")
            case State.NETWORK_ERROR:
                await channel.edit(name=f"❓ Network Error")