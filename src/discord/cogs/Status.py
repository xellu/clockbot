import discord
from discord import Embed, app_commands
from discord.ext import commands, tasks
from enum import Enum

from src.lib.Discord import AddCog
from src.lib.Colors import *
from src.lib.User import UserManager
from src.lib.Util import escape_md
from src.lib.Clockwork import CW

from nautica import Services, Config, Logger
from plugins.CWEvents import PlayerJoinEvent

class State(Enum):
    OFFLINE = 0
    ONLINE = 1
    MAINTENANCE = 2

class StatusChannels:
    def __init__(self, tps: discord.VoiceChannel, state: discord.VoiceChannel):
        self.tps = tps
        self.state = state
        
def getTpsEmoji(tps: float):
    if tps > 19: return "🤩"
    if tps > 17: return "😁"
    if tps > 15: return "🙂"
    if tps > 13: return "🙄"
    if tps > 11: return "😥"
    if tps > 7: return "😞"
    if tps > 5: return "😡"
    return "😵"

MESSAGES = {
    "ONLINE": "Server is online",
    "OFFLINE": "Server went offline",
    "MAINTENANCE": "Server is under maintenance"
}

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        
        self.channels: StatusChannels = None
        self.state: State = None
        self.last_state: State = None
        
        self.maintenance = False
        
        CW.onPlayerJoin()(self.on_player_join)
        
    async def cog_load(self):
        self.update_status.start()
        self.update_channels.start()

    async def getChannels(self) -> StatusChannels:
        if self.channels is None:
            tps = await self.bot.fetch_channel(Config("clockbot")["status.tpsChannelId"])
            state = await self.bot.fetch_channel(Config("clockbot")["status.stateChannelId"])

            self.channels = StatusChannels(tps, state)
            
        return self.channels
        
    @tasks.loop(seconds=300)
    async def update_channels(self):
        await self._update_channels(self.state)
    
    async def _update_channels(self, state):
        channels: StatusChannels = await self.getChannels()
        
        match state:
            case State.ONLINE:
                await channels.state.edit(name=f"{'🔥' if CW.status['online']['count'] > 10 else '🟢'} Online")
                await channels.tps.edit(name=f"{getTpsEmoji(CW.status['tps'])} TPS: {CW.status['tps']:.1f}")  
        
            case State.OFFLINE:
                await channels.state.edit(name=f"⛔ Server Offline")
                await channels.tps.edit(name=f"🤔 TPS: N/A")
    
            case State.MAINTENANCE:
                await channels.state.edit(name=f"🔄️ Maintenance")
                await channels.tps.edit(name=f"🤔 TPS: N/A")

    @tasks.loop(seconds=10)
    async def update_status(self):
        if self.maintenance: self.state = State.MAINTENANCE
        elif CW.logged_in: self.state = State.ONLINE
        else: self.state = State.OFFLINE
        
        
        if self.last_state != self.state:
            Logger.info(f"Updated status {self.last_state.name if self.last_state else 'NONE'} -> {self.state.name}")
            c = await self.bot.fetch_channel(Config("clockbot")["chatlink.channelId"])
            if c:
                await c.send(embed=Embed(
                    description = f"**{MESSAGES.get(self.state.name)}**",
                    color = OK if self.state == State.ONLINE else (INFO if self.self.maintenance else ERROR)
                ))
        
        self.last_state = self.state

    async def on_player_join(self, event: PlayerJoinEvent):
        # if not self.maintenance: return
        
        # u = UserManager(minecraft=event.player.uuid)
        # if not u.is_valid():
        #     CW.KickPlayer(event.player.uuid, "Maintenance")
        #     return
        
        # if not isStaff(u):
        #     CW.KickPlayer(event.player.uuid, "Maintenance")
        #     return
        pass
        
    @app_commands.command(name="maintenance", description="Sets the server into a maintenance state")
    @app_commands.describe(reason="The reason for the maintenance", ping="Whether to ping members")
    @app_commands.allowed_contexts(guilds=True, private_channels=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def set_maintenance(self, ctx: discord.Interaction, reason: str = None, ping: bool = False):
        channel = await self.bot.fetch_channel(Config("clockbot")["announcements.channelId"])
        
        #enable maintenance ---------
        if not self.maintenance:
            await channel.send(f"@here" if ping else "",
                embed = Embed(
                    title = "Server Maintenance",
                    description = "⚠️ The server is going into maintenance mode!\n> " + reason if reason else "`No further information provided`",
                    color = WARN
                ) \
                    .set_footer(text="You will be notified when the server is back online") \
                    .set_author(name=ctx.user.name, icon_url=ctx.user.display_avatar.url)
            )
                
            await ctx.response.send_message(embed=Embed(
                title = "Maintenance",
                description = "✅ Maintenance mode enabled",
                color = OK
            ))
            self.maintenance = True
            await self._update_channels(State.MAINTENANCE)
            return
    
        #disable----------
        await channel.send(f"@here" if ping else None,
            embed=Embed(
                title = "Server Maintenance",
                description = "✅ The server is back online!",
                color = OK
        ))
        self.maintenance = False
        await self._update_channels(State.ONLINE if CW.logged_in else State.OFFLINE)
        
    
    @app_commands.command(name="tps", description="Shows the current TPS (Ticks per Second) of the server")
    @app_commands.allowed_contexts(guilds=True, private_channels=True)
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild.id if i.guild else i.user.id))
    async def tps_command(self, ctx):        
        await ctx.response.defer(thinking=True)
    
        if not CW.logged_in:
            await ctx.followup.send(embed=Embed(
                title = "Server Status",
                description = "❌ Failed to get server TPS\n> *The server is offline, or the API is unreachable*",
                color = ERROR
            ))
            return
        
        await ctx.followup.send(embed=Embed(
            title = "Server Status",
            description = f"The current TPS is `{CW.status['tps']:.1f}`",
            color = INFO
        ))
            
    @app_commands.command(name="online", description="Lists the players currently online")
    @app_commands.allowed_contexts(guilds=True, private_channels=True)
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild.id if i.guild else i.user.id))
    async def online_command(self, ctx):        
        await ctx.response.defer(thinking=True)
            
        if not CW.logged_in:
            await ctx.followup.send(embed=Embed(
                title = "Online Players",
                description = "❌ Failed to get online players\n> *The server is offline, or the API is unreachable*",
                color = ERROR
            ))
            return
        
        await ctx.followup.send(embed=Embed(
            title = "Online Players",
            description = f"""*There are {CW.status['online']['count']} players online at this moment*\n\n{', '.join(escape_md(p['name']) for p in CW.status['online']['list'])}\n""",
            color = INFO
        ))
        
AddCog(Status)