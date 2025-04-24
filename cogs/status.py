from discord.ext import commands, tasks
from discord import app_commands, Embed

from mdbb import Bot, Config, CommandLogger, Colors
from plugins.puffer import Puffer

import requests
import enum
import time

class State(enum.Enum):
    NETWORK_ERROR = -1
    OFFLINE = 0
    ONLINE = 1
    MAINTENANCE = 2


class Status(commands.Cog):
    def __init__(self):
        self.bot = Bot
        self.maintenance = False
        self.last_state = None
        
        self.players_max = 0
        self.players_online = 0
        
        if not Config.get("MODULES.STATUS"): return
        self.update_status.start()
    
    #SERVER STATUS DISPLAY----------------------------------
    @tasks.loop(seconds=300)
    async def update_status(self):
        r = requests.get(f"https://api.mcstatus.io/v2/status/java/{Config.get('STATUS.TARGET.IP')}")
        if r.status_code != 200:
            await self.set_channel_status(State.NETWORK_ERROR)
            return
        
        if self.maintenance:
            await self.set_channel_status(State.MAINTENANCE)
            return
        
        data = r.json()
        if data["online"]:
            self.players_online = data["players"]["online"]
            self.players_max = data["players"]["max"]
            
            await self.set_channel_status(State.ONLINE)
            return
        
        await self.set_channel_status(State.OFFLINE)
        
            
    async def set_channel_status(self, state):
        channel = await self.bot.fetch_channel(Config.get("STATUS.STATE.CHANNEL"))
            
        match state:
            case State.ONLINE:
                await channel.edit(name=f"{'🔥' if self.players_online >= 10 else '🟢'} Online: {self.players_online}")
            case State.OFFLINE:
                await channel.edit(name=f"⛔ Server Offline")
            case State.MAINTENANCE:
                await channel.edit(name=f"⚠️ Maintenance")
            case State.NETWORK_ERROR:
                await channel.edit(name=f"❓ API Error")
        
        if state != self.last_state:
            CommandLogger.ok(f"Status: updated server status to {state.name} ({self.players_online}/{self.players_max})")        

        self.last_state = state

    #MAINTENANCE ----------------------------------
    @app_commands.command(name="maintenance", description="Sets the server into a maintenance state")
    @app_commands.describe(reason="The reason for the maintenance", ping="Whether to ping members")
    @app_commands.allowed_contexts(guilds=True, private_channels=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def maintenance_command(self, ctx, reason: str = None, ping: bool = False):
        channel = await self.bot.fetch_channel(Config.get("STATUS.ANNOUNCE.CHANNEL"))
        
        #enable maintenance
        if not self.maintenance:
            embed = Embed(
                title = "Server Maintenance",
                description = "⚠️ The server is going into maintenance mode!\n> " + reason if reason else "`No further information provided`",
                color = Colors.WARNING
            )
            embed.set_footer(text="You will be notified when the server is back online")
            embed.set_author(name=ctx.user.name, icon_url=ctx.user.display_avatar.url)
            
            if ping:
                await channel.send(f"@here", embed=embed)
            else:
                await channel.send(embed=embed)
                
            await ctx.response.send_message(embed=Embed(
                title = "Maintenance",
                description = "✅ Maintenance mode enabled",
                color = Colors.OK
            ))
            self.maintenance = True
            await self.set_channel_status(State.MAINTENANCE)
            return
        
        #disable maintenance
        embed = Embed(
            title = "Server Maintenance",
            description = "✅ The server is back online!",
            color = Colors.OK
        )
        
        if ping:
            await channel.send(f"@here", embed=embed)
        else:
            await channel.send(embed=embed)
            
        await ctx.response.send_message(embed=Embed(
            title = "Maintenance",
            description = "✅ Maintenance mode disabled",
            color = Colors.OK
        ))
        self.maintenance = False
        await self.set_channel_status(State.ONLINE)
        
    #SERVER INFO----------------------------------
    @app_commands.command(name="tps", description="Shows the current TPS (Ticks per Second) of the server")
    @app_commands.allowed_contexts(guilds=True, private_channels=True)
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild.id if i.guild else i.user.id))
    async def tps_command(self, ctx):
        if not Config.get("MODULES.STATUS"):
            await ctx.response.send_message(embed=Embed(
                title = "Server Status",
                description = "❌ This command is disabled",
                color = Colors.ERROR
            ))
            return
        
        
        await ctx.response.defer(thinking=True)
    
        Puffer.execute_command("spark tps")
        
        tps = {"tps": None, "expire": time.time()+5}
        while True:
            if time.time() > tps["expire"]:
                break
            
            if time.time() - Puffer.tps["last_updated"] < 10:
                tps["tps"] = Puffer.tps["tps"]
                break
            
        if tps["tps"] is None:
            await ctx.followup.send(embed=Embed(
                title = "Server Status",
                description = "❌ Failed to get TPS data",
                color = Colors.ERROR
            ))
            return
        
        await ctx.followup.send(embed=Embed(
            title = "Server Status",
            description = f"The current TPS is `{tps['tps']}`",
            color = Colors.DEFAULT
        ))
            
    @app_commands.command(name="online", description="Lists the players currently online")
    @app_commands.allowed_contexts(guilds=True, private_channels=True)
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild.id if i.guild else i.user.id))
    async def online_command(self, ctx):
        if not Config.get("MODULES.STATUS"):
            await ctx.response.send_message(embed=Embed(
                title = "Online Players",
                description = "❌ This command is disabled",
                color = Colors.ERROR
            ))
            return
        
        
        await ctx.response.defer(thinking=True)
    
        Puffer.execute_command("list")
        
        online = {
            "players": [],
            "online": None,
            "max": None,
            "expire": time.time()+5
        }
        while True:
            if time.time() > online["expire"]:
                break
            
            if time.time() - Puffer.players["last_updated"] < 10:
                online = Puffer.players
                break
            
        if online["online"] is None:
            await ctx.followup.send(embed=Embed(
                title = "Online Players",
                description = "❌ Failed to get player data",
                color = Colors.ERROR
            ))
            return
        
        await ctx.followup.send(embed=Embed(
            title = "Online Players",
            description = f"""*There are {online["online"]} players online out of {online["max"]} max players*\n\n{', '.join(online["players"])}\n""",
            color = Colors.DEFAULT
        ))