from discord.ext import commands, tasks
from discord import app_commands, Embed
import discord as _discord

from mdbb import DB, Config, Bot, Colors, CommandLogger

from plugins.cwcore import CWCore, CWChatMessage

from core.templates.UserTemplate import WLStatus
from core.templates.PunishmentTemplate import WarnTemplate, KickTemplate, BanTemplate

from core import WORD_BLACKLIST
from core.utils import parse_time, escape_md, get_mc_username, get_mc_uuid
from core.users import UserManager

import time

class Moderation(commands.Cog):
    def __init__(self):
        self.bot = Bot
        self.warn_queue = [] #for chat warnings from Minecraft
        
        self.auto_mod_channel = self.bot.get_channel(Config.get("AUTOMOD.ANNOUNCE.CHANNEL"))
        if not self.auto_mod_channel:
            CommandLogger.error("AutoMod: Announcement channel not found, please check your config")
            return
        
        self.enabled = Config.get("MODULES.AUTOMOD")
        if not self.enabled:
            CommandLogger.warning("Module disabled: AutoMod")
            return
        
        CWCore.event.register("chat.message", self.on_minecraft_message)
        CWCore.event.register("player.join", self.on_minecraft_join)
        
        self.warn_loop.start()
    
    #automod warning system
    @tasks.loop(seconds=5)
    async def warn_loop(self):
        for warn in self.warn_queue:
            await self.process_warning(
                warn["user"],
                warn["reason"],
                moderator=warn.get("moderator", None),
                reference = warn.get("reference", None)
            )
            self.warn_queue.remove(warn)
            
    def on_minecraft_join(self, data: dict):
        if not self.enabled: return
        
        user = UserManager(minecraft=data['uuid'])
        if not user.is_valid() or user.get()["whitelist"]["status"] != WLStatus.APPROVED.value:
            CommandLogger.warn(f"User {data['uuid']} is not valid, kicking from server")
            CWCore.kick_player(data['uuid'], "[ClockMod] Unable to find your ClockAPI Profile, please contact an admin")
            return
        
        is_banned = user.is_banned()
        
        if is_banned.ok:
            CommandLogger.warn(f"User {data['uuid']} ({user.get()['minecraft']}) is banned, kicking from server")
            if is_banned.meta.get("expires_at"):
                expires_at = parse_time(int(is_banned.meta["expires_at"]) - time.time())
                CWCore.kick_player(data['uuid'], f"[ClockMod] You are banned for {expires_at}.\nReason: {is_banned.meta['reason']}")
                return
            CWCore.kick_player(data['uuid'], f"[ClockMod] You are permanently banned.\nReason: {is_banned.meta['reason']}")
        
    def on_minecraft_message(self, msg: dict):
        if not self.enabled: return
        
        for word in msg['content'].split(" "):
            if word.lower() in WORD_BLACKLIST:
                user = UserManager(minecraft=msg['author']['uuid'])
                CommandLogger.warn(f"Flagged message from {msg['author']['name']} ({msg['author']['uuid']}) for '{word}': {msg['content']}")
                
                self.warn_queue.append({
                    "user": user,
                    "reason": f"Inappropriate language",
                    "reference": f"Flagged {word} in '{msg['content']}'"
                })
                return
    
    #helpers
    async def is_exempt(self, user: UserManager) -> bool:
        member = self.bot.get_guild(Config.get("WHITELIST.MONITOR.GUILD")).get_member(user.get()["discord"])
        if not member:
            return False
        
        for role in member.roles:
            if role.id in Config.get("AUTOMOD.IGNORE"): return True
        return False
            
    #processing functions for punishments
    async def process_warning(self, user: UserManager, reason: str = "No reason provided", moderator: int = None, expire_in: int = None, reference: str = None):
        if not user.is_valid():
            CommandLogger.error(f"User {user.get()['minecraft']} is not valid, skipping warning")
            return
        
        if await self.is_exempt(user):
            return
        
        warn = WarnTemplate()
        warn.update({
            "user": user.get()["discord"],
            "moderator": moderator or None,
            
            "reason": reason,
            "expires_at": time.time() + (expire_in or Config.get("AUTOMOD.WARNINGS.EXPIRE")),
        })
        
        DB.get("clockbot").mod.insert_one(warn)
        
        CommandLogger.warn(f"Warning issued to {user.get()['minecraft']} ({user.get()['discord']}) by {moderator or 'AutoMod'}: {reason}")
        await self.auto_mod_channel.send(
            embed=Embed(
                title = "Warning",
                description = f"**User:** {escape_md(get_mc_username(user.get()['minecraft']))} <@{user.get()['discord']}>\n"
                            f"**Moderator:** {moderator or 'AutoMod'}\n"
                            f"**Reason:** `{reason}`\n"
                            f"**Expires at:** <t:{int(warn['expires_at'])}:R>"
                            f"{'\n\n**Reference:** `' + reference + '`' if reference else ''}",
                            
                color = Colors.WARNING 
            )
            .set_footer(text=f"ID: {warn['id']}")
            .set_author(
                name = "AutoMod" if not moderator else self.bot.get_user(moderator).display_name,
                icon_url = self.bot.user.display_avatar.url if not moderator else self.bot.get_user(moderator).display_avatar.url
            )
        )
        
        active_warns = DB.get("clockbot").mod.find({
            "user": user.get()["discord"],
            "type": "warn",
            "expires_at": {"$gt": time.time()}
        })
        
        if len(list(active_warns)) >= Config.get("AUTOMOD.WARNINGS.KICK"):
            await self.process_kick(user, f"Exceeded warning limit ({Config.get('AUTOMOD.WARNINGS.KICK')})", moderator)
        
        if len(list(active_warns)) >= Config.get("AUTOMOD.WARNINGS.BAN"):
            await self.process_ban(user, f"Exceeded warning limit ({Config.get('AUTOMOD.WARNINGS.BAN')})", moderator)
            
        if user.get_seen().meta == -2:
            CWCore.chat_passthrough(CWChatMessage(
                message_id=0,
                author = "AutoMod",
                content = f"\n========================\n\n{get_mc_username(user.get()['minecraft'])} has been warned\nReason: {reason}\nExpires in: {parse_time(int(warn['expires_at']) - time.time())}\n\n========================\n"
            ))
            
    async def process_kick(self, user: UserManager, reason: str = "No reason provided", moderator: int = None):
        if not user.is_valid():
            CommandLogger.error(f"User {user.get()['minecraft']} is not valid, skipping kick")
            return
        
        if await self.is_exempt(user):
            return
        
        kick = KickTemplate()
        kick.update({
            "user": user.get()["discord"],
            "moderator": moderator or None,
            
            "reason": reason
        })
        
        DB.get("clockbot").mod.insert_one(kick)
        
        CommandLogger.warn(f"Kick issued to {user.get()['minecraft']} ({user.get()['discord']}) by {moderator or 'AutoMod'}: {reason}")
        await self.auto_mod_channel.send(
            embed=Embed(
                title = "Kick",
                description = f"**User:** {escape_md(get_mc_username(user.get()['minecraft']))} <@{user.get()['discord']}>\n"
                            f"**Moderator:** {moderator or 'AutoMod'}\n"
                            f"**Reason:** `{reason}`",
                color = Colors.WARNING
            )
            .set_footer(text=f"ID: {kick['id']}")
            .set_author(
                name = "AutoMod" if not moderator else self.bot.get_user(moderator).display_name,
                icon_url = self.bot.user.display_avatar.url if not moderator else self.bot.get_user(moderator).display_avatar.url
            )
        )
        
        if user.get_seen().meta == -2:    
            CWCore.chat_passthrough(CWChatMessage(
                message_id=0,
                author = "AutoMod",
                content = f"\n========================\n\n{get_mc_username(user.get()['minecraft'])} has been kicked from the server\nReason: {reason}\n\n========================\n"
            ))
            CWCore.kick_player(get_mc_username(user.get()["minecraft"]), reason)
            
    
    async def process_ban(self, user: UserManager, reason: str = "No reason provided", moderator: int = None, expire_in: int = 0):
        """
        Bans a user from the server.
        Args:
            user (UserManager): The user to ban.
            reason (str): The reason for the ban.
            moderator (int, optional): The ID of the moderator issuing the ban. Defaults to None (AutoMod).
            expire_in (int, optional): Time in seconds until the ban expires. Defaults to 0 (Config default). Use None for permanent bans.
        """
        if not user.is_valid():
            CommandLogger.error(f"User {user.get()['minecraft']} is not valid, skipping ban")
            return
        
        if await self.is_exempt(user):
            return
        
        ban = BanTemplate()
        ban.update({
            "user": user.get()["discord"],
            "moderator": moderator or None,
            
            "reason": reason,
            "expires_at": time.time() + (expire_in or Config.get("AUTOMOD.BANS.EXPIRE")) if expire_in is not None else None,
        })
        
        DB.get("clockbot").mod.insert_one(ban)
        
        CommandLogger.warn(f"Ban issued to {user.get()['minecraft']} ({user.get()['discord']}) by {moderator or 'AutoMod'}: {reason}")
        await self.auto_mod_channel.send(
            embed=Embed(
                title = "Ban",
                description = f"**User:** {escape_md(get_mc_username(user.get()['minecraft']))} <@{user.get()['discord']}>\n"
                            f"**Moderator:** {moderator or 'AutoMod'}\n"
                            f"**Reason:** `{reason}`\n"
                            f"**Expires at:** {'<t:' + str(int(ban['expires_at'])) + ':R>' if ban['expires_at'] else 'Permanent'}",
                color = Colors.ERROR
            )
            .set_footer(text=f"ID: {ban['id']}")
            .set_author(
                name = "AutoMod" if not moderator else self.bot.get_user(moderator).display_name,
                icon_url = self.bot.user.display_avatar.url if not moderator else self.bot.get_user(moderator).display_avatar.url
            )
        )
        
        if user.get_seen().meta == -2:
            CWCore.chat_passthrough(CWChatMessage(
                message_id=0,
                author = "AutoMod",
                content = f"\n========================\n\n{get_mc_username(user.get()['minecraft'])} has been banned from the server\nReason: {reason}\nExpires in: {parse_time(int(ban['expires_at']) - time.time()) if ban['expires_at'] else 'Permanent'}\n\n========================\n"
            ))
            CWCore.kick_player(get_mc_username(user.get()["minecraft"]), reason)
            
        if expire_in is None:
            user.whitelist_remove(self.bot.user.id)
            member = self.bot.get_guild(Config.get("WHITELIST.MONITOR.GUILD")).get_member(user.get()["discord"])
            if member:
                await member.remove_roles(Config.get("WHITELIST.MEMBERSHIP.ROLE"))
    
    
    #commands-------
    @app_commands.command(name="mod-history", description="View the punishment history of a user")
    @app_commands.guild_only()
    @app_commands.checks.has_any_role(*Config.get("AUTOMOD.ADMINS"))
    @app_commands.describe(discord="Discord user to check", minecraft="Minecraft username to check")
    async def mod_history(self, ctx: _discord.Interaction, discord: _discord.User = None, minecraft: str = None):
        if not discord and not minecraft:
            await ctx.response.send_message(embed=Embed( description = "Please provide either a Discord user or a Minecraft username.", color = Colors.ERROR ))
            return
        
        await ctx.response.defer()
        
        if discord: user = UserManager(discord=discord.id)
        elif minecraft: user = UserManager(minecraft=get_mc_uuid(minecraft))
        
        if not user.is_valid():
            await ctx.followup.send(embed=Embed(
                description = "User not found",
                color = Colors.ERROR
            ))
            return
        
        punishments = DB.get("clockbot").mod.find({"user": user.get()["discord"]})
        
        if not punishments:
            await ctx.followup.send(embed=Embed(
                description = "No history found for this user",
                color = Colors.OK
            ))
            return
        
        out = []
        for p in punishments:
            active = True if p.get('expires_at') is None or p['expires_at'] > time.time() else False
            if p["type"] == "kick": active = False  # Kicks are always considered expired
            
            duration = "Forever" if p.get('expires_at') is None else parse_time(int(p['expires_at'] - p['created_at']))
            
            out.append(f"""{"`❗ ACTIVE`" if active else "`✅ EXPIRED`"} **{p['type'].capitalize()} for {duration}** - ID: {p['id']}\n> Issued at <t:{int(p['created_at'])}:F> by {self.bot.get_user(p['moderator']).mention if p.get('moderator') else '`AutoMod`'}\n> Reason: `{p['reason']}`""")

        embed = Embed(
            title = f"Punishment History for {get_mc_username(user.get()['minecraft'])}",
            description = "\n\n".join(out),
            color = Colors.DEFAULT
        )
        embed.set_footer(text=f"Total: {len(out)} punishments")
        await ctx.followup.send(embed=embed)
        
    @app_commands.command(name="mod-clear", description="Clear all punishments for a user")
    @app_commands.guild_only()
    @app_commands.checks.has_any_role(*Config.get("AUTOMOD.ADMINS"))
    @app_commands.describe(discord="Discord user to clear", minecraft="Minecraft username to clear")
    async def mod_clear(self, ctx: _discord.Interaction, discord: _discord.User = None, minecraft: str = None):
        if not discord and not minecraft:
            await ctx.response.send_message(embed=Embed( description = "Please provide either a Discord user or a Minecraft username.", color = Colors.ERROR ))
            return
        
        await ctx.response.defer()
        
        if discord: user = UserManager(discord=discord.id)
        elif minecraft: user = UserManager(minecraft=get_mc_uuid(minecraft))
        
        if not user.is_valid():
            await ctx.followup.send(embed=Embed(
                description = "User not found",
                color = Colors.ERROR
            ))
            return
        
        DB.get("clockbot").mod.delete_many({"user": user.get()["discord"]})
        
        await ctx.followup.send(embed=Embed(
            description = f"Cleared all punishments for {get_mc_username(user.get()['minecraft'])}",
            color = Colors.OK
        ))
        
    @app_commands.command(name="mod-undo", description="Undo a punishment for a user")
    @app_commands.guild_only()
    @app_commands.checks.has_any_role(*Config.get("AUTOMOD.ADMINS"))
    @app_commands.describe(punishment_id="ID of the punishment to undo")
    async def mod_undo(self, ctx: _discord.Interaction, punishment_id: str):
        res = DB.get("clockbot").mod.find_one({"id": punishment_id})
        if not res:
            await ctx.response.send_message(embed=Embed(
                description = "Punishment not found",
                color = Colors.ERROR
            ))
            return
        
        DB.get("clockbot").mod.delete_one({"id": punishment_id})
        await ctx.response.send_message(embed=Embed(
            description = f"Undid punishment `{punishment_id}` for user {get_mc_username(UserManager(discord=res['user']).get()['minecraft'])}",
            color = Colors.OK
        ))
        
    @app_commands.command(name="mod-warn", description="Warn a user in the minecraft server")
    @app_commands.guild_only()
    @app_commands.checks.has_any_role(*Config.get("AUTOMOD.ADMINS"))
    @app_commands.describe(discord="Discord user to warn", minecraft="Minecraft username to warn", reason="Reason for the warning")
    async def mod_warn(self, ctx: _discord.Interaction, discord: _discord.User = None, minecraft: str = None, reason: str = "No reason provided"):
        if not discord and not minecraft:
            await ctx.response.send_message(embed=Embed( description = "Please provide either a Discord user or a Minecraft username.", color = Colors.ERROR ))
            return
        
        await ctx.response.defer()
        
        if discord: user = UserManager(discord=discord.id)
        elif minecraft: user = UserManager(minecraft=get_mc_uuid(minecraft))
        
        if not user.is_valid():
            await ctx.followup.send(embed=Embed(
                description = "User not found",
                color = Colors.ERROR
            ))
            return
        
        await self.process_warning(user, reason, ctx.user.id)
        
        await ctx.followup.send(embed=Embed(
            description = f"Warned {get_mc_username(user.get()['minecraft'])}",
            color = Colors.OK
        ))
        
    @app_commands.command(name="mod-kick", description="Kick a user from the minecraft server")
    @app_commands.guild_only()
    @app_commands.checks.has_any_role(*Config.get("AUTOMOD.ADMINS"))
    @app_commands.describe(discord="Discord user to kick", minecraft="Minecraft username to kick", reason="Reason for the kick")
    async def mod_kick(self, ctx: _discord.Interaction, discord: _discord.User = None, minecraft: str = None, reason: str = "No reason provided"):
        if not discord and not minecraft:
            await ctx.response.send_message(embed=Embed( description = "Please provide either a Discord user or a Minecraft username.", color = Colors.ERROR ))
            return
        
        await ctx.response.defer()
        
        if discord: user = UserManager(discord=discord.id)
        elif minecraft: user = UserManager(minecraft=get_mc_uuid(minecraft))
        
        if not user.is_valid():
            await ctx.followup.send(embed=Embed(
                description = "User not found",
                color = Colors.ERROR
            ))
            return
        
        await self.process_kick(user, reason, ctx.user.id)
        
        await ctx.followup.send(embed=Embed(
            description = f"Kicked {get_mc_username(user.get()['minecraft'])} from the server",
            color = Colors.OK
        ))
        
    @app_commands.command(name="mod-ban", description="Ban a user from the minecraft server")
    @app_commands.guild_only()
    @app_commands.checks.has_any_role(*Config.get("AUTOMOD.ADMINS"))
    @app_commands.describe(discord="Discord user to ban", minecraft="Minecraft username to ban", reason="Reason for the ban", expire_in="Time for the ban to expire")
    @app_commands.choices(expire_in=[
        app_commands.Choice(name="Permanent", value=-1),
        app_commands.Choice(name="1 hour", value=3600),
        app_commands.Choice(name="6 hours", value=21600),
        app_commands.Choice(name="12 hours", value=43200),
        app_commands.Choice(name="1 day", value=86400),
        app_commands.Choice(name="3 days", value=259200),
        app_commands.Choice(name="1 week", value=604800),
        app_commands.Choice(name="2 weeks", value=1209600),
        app_commands.Choice(name="1 month", value=2592000),
        app_commands.Choice(name="3 months", value=7776000),
        app_commands.Choice(name="6 months", value=15552000),
        app_commands.Choice(name="1 year", value=31536000),
    ])
    async def mod_ban(self, ctx: _discord.Interaction, discord: _discord.User = None, minecraft: str = None, reason: str = "No reason provided", expire_in: int = 0):
        if not discord and not minecraft:
            await ctx.response.send_message(embed=Embed( description = "Please provide either a Discord user or a Minecraft username.", color = Colors.ERROR ))
            return
        
        await ctx.response.defer()
        
        if discord: user = UserManager(discord=discord.id)
        elif minecraft: user = UserManager(minecraft=get_mc_uuid(minecraft))
        
        if expire_in == -1: expire_in = None
        
        if not user.is_valid():
            await ctx.followup.send(embed=Embed(
                description = "User not found",
                color = Colors.ERROR
            ))
            return
        
        await self.process_ban(user, reason, ctx.user.id, expire_in)
        
        await ctx.followup.send(embed=Embed(
            description = f"Banned {get_mc_username(user.get()['minecraft'])} from the server",
            color = Colors.OK
        ))
        
