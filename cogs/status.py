from discord.ext import commands, tasks
from discord import app_commands, Embed

from mdbb import Bot, Config, CommandLogger, Colors
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
        self.maintenance = False
        self.last_state = None
        
        self.update_status.start()
    
    #SERVER STATUS DISPLAY----------------------------------
    @tasks.loop(seconds=60)
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
            await self.set_channel_status(State.ONLINE, data["players"]["online"])
            return
        
        #TODO: make maintenance work
        await self.set_channel_status(State.OFFLINE)
        
            
    async def set_channel_status(self, state, players = None):
        channel = await self.bot.fetch_channel(Config.get("STATUS.STATE.CHANNEL"))
            
        match state:
            case State.ONLINE:
                await channel.edit(name=f"{'🔥' if players > 10 else '🌐'} {players} Online")
            case State.OFFLINE:
                await channel.edit(name=f"⛔ Server Offline")
            case State.MAINTENANCE:
                await channel.edit(name=f"⚠️ Maintenance")
            case State.NETWORK_ERROR:
                await channel.edit(name=f"❓ API Error")
        
        if state != self.last_state:
            CommandLogger.ok(f"Status: updated server status to {state.name} ({players})")        

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