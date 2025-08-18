from discord.ext import commands, tasks
from discord import app_commands, Embed

from mdbb import Bot, Config, CommandLogger, Colors, EventBus

from core.utils import escape_md
from plugins.cwcore import CWCore

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
        
        if not Config.get("MODULES.STATUS"):
            CommandLogger.warning("Module disabled: Status")
            return
        self.update_status.start()
    
    #SERVER STATUS DISPLAY----------------------------------
    @tasks.loop(seconds=300)
    async def update_status(self):
        if self.maintenance:
            await self.set_channel_status(State.MAINTENANCE)
            return
        
        if CWCore.logged_in:
            await self.set_channel_status(State.ONLINE)
            return
        
        await self.set_channel_status(State.OFFLINE)
        
            
    async def set_channel_status(self, state):
        state_channel = await self.bot.fetch_channel(Config.get("STATUS.STATE.CHANNEL"))
        tps_channel = await self.bot.fetch_channel(Config.get("STATUS.TPS.CHANNEL"))
        
            
        match state:
            case State.ONLINE:
                await state_channel.edit(name=f"{'🔥' if CWCore.status['online']['count'] >= 10 else '🟢'} Online: {CWCore.status['online']['count']}")
                await tps_channel.edit(name=f"{'🥳' if CWCore.status['tps'] >= 10 else '😰'} TPS: {CWCore.status['tps']:.1f}")
            case State.OFFLINE:
                await state_channel.edit(name=f"⛔ Server Offline")
                await tps_channel.edit(name=f"❓ TPS: N/A")
            case State.MAINTENANCE:
                await state_channel.edit(name=f"🔄️ Maintenance")
                await tps_channel.edit(name=f"❓ TPS: N/A")
            case State.NETWORK_ERROR:
                await state_channel.edit(name=f"❓ API Error")
                await tps_channel.edit(name=f"❓ TPS: N/A")
        
        if state != self.last_state:
            CommandLogger.ok(f"Status: updated server status to {state.name} ({CWCore.status['online']['count']}/{CWCore.status['online']['max']})")        

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
                await channel.send(f"<@&1405226979673899049>", embed=embed)
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
            await channel.send(f"<@&1405226979673899049>", embed=embed)
        else:
            await channel.send(embed=embed)
            
        await ctx.response.send_message(embed=Embed(
            title = "Maintenance",
            description = "✅ Maintenance mode disabled",
            color = Colors.OK
        ))
        self.maintenance = False
        await self.set_channel_status(State.ONLINE)
        
    @app_commands.command(name="stop", description="Stops the Discord bot")
    @app_commands.allowed_contexts(guilds=True, private_channels=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def stop_command(self, ctx):
        await ctx.response.send_message(embed=Embed(description="Shutting down...", color=Colors.DEFAULT))
        EventBus.emit("shutdown", f"Shutdown requested by {ctx.user.name} ({ctx.user.id})")
        
        
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
            ), ephemeral=True)
            return
        
        
        await ctx.response.defer(thinking=True)
    
        if not CWCore.logged_in:
            await ctx.followup.send(embed=Embed(
                title = "Server Status",
                description = "❌ Failed to get server TPS\n> *The server is offline, or the API is unreachable*",
                color = Colors.ERROR
            ))
            return
        
        await ctx.followup.send(embed=Embed(
            title = "Server Status",
            description = f"The current TPS is `{CWCore.status['tps']:.1f}`",
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
            ), ephemeral=True)
            return
        
        
        await ctx.response.defer(thinking=True)
            
        if not CWCore.logged_in:
            await ctx.followup.send(embed=Embed(
                title = "Online Players",
                description = "❌ Failed to get online players\n> *The server is offline, or the API is unreachable*",
                color = Colors.ERROR
            ))
            return
        
        await ctx.followup.send(embed=Embed(
            title = "Online Players",
            description = f"""*There are {CWCore.status['online']['count']} players online at this moment*\n\n{', '.join(escape_md(p['name']) for p in CWCore.status['online']['list'])}\n""",
            color = Colors.DEFAULT
        ))