from discord.ext import commands, tasks
from discord import app_commands, Embed
import time
import re

from mdbb import Bot, Config, CommandLogger, Colors, DB
from core import WORD_BLACKLIST
from core.utils import get_mc_username, get_mc_uuid, random_str, parse_time, escape_md
from core.users import UserManager
from core.templates.PunishmentTemplate import WarnTemplate

from plugins.cwcore import CWCore, CWChatMessage
from plugins.word_blacklist import FlagMan

#xaero-waypoint:<name>:<initial>:<x>:<y>:<z>:<color_id>:<disabled>:<type>:<dimension_id>
WP_REGEX = re.compile(r"xaero-waypoint:(.+?):(.+?):(.+?):(.+?):(.+?):(.+?):(.+?):(.+?):(.+)")

class CLMessage:
    def __init__(self, content=None, embed = None):
        self.content = content
        self.embed = embed

class CLCommand:
    def __init__(self, name, description, args, func):
        self.name = name
        self.description = description
        self.args = args
        self.func = func
        
class CLCArgs:
    def __init__(self, name, required = True):
        self.name = name
        self.required = required
        
class ChatLink(commands.Cog):
    def __init__(self):
        self.bot = Bot
        self.channel = self.bot.get_channel(Config.get("CHATLINK.CHANNEL"))
        
        if not Config.get("MODULES.CHATLINK"):
            CommandLogger.warning("Module disabled: ChatLink")
            return
        
        if not self.channel:
            CommandLogger.error("ChatLink: Channel not found, please check your config")
        
        self.queue = []
        self.queue_loop.start()
        
        self.commands = {
            CLCommand("help", "Show available commands", [], self.cmd_help),
            CLCommand("seen", "Check when was a player last seen", [CLCArgs("player")], self.cmd_seen),
            CLCommand("warn", "Warn a player", [CLCArgs("player"), CLCArgs("*reason")], self.cmd_warn),
        }
        
        CWCore.event.register("chat.message", self.on_chat_message)
        CWCore.event.register("player.join", self.on_player_join)
        CWCore.event.register("player.leave", self.on_player_leave)
        CWCore.event.register("conn.open", self.on_conn_open)
        CWCore.event.register("conn.drop", self.on_conn_close)
        
    @tasks.loop(seconds=1)
    async def queue_loop(self):
        for msg in self.queue:            
            if msg.embed:
                await self.channel.send(embed=msg.embed)
                continue
            
            msg.content = FlagMan.censor(msg.content)
            await self.channel.send(msg.content.replace("@", "@\u200b"))
                
        self.queue.clear()
        
    @commands.Cog.listener()
    async def on_message(self, msg):
        """
        Handle incoming messages from Discord and forward them to the CWCore API.
        """
        
        if msg.author.bot: return
        if msg.channel.id != Config.get("CHATLINK.CHANNEL"): return
        if not Config.get("MODULES.CHATLINK"): return
        
        cwm = CWChatMessage(
            message_id = msg.id,
            author = self.minecraft_username(msg.author),
            content = msg.content.replace("**", ""),
            attachments = [attachment.url for attachment in msg.attachments],
        )
        if msg.reference:
            ref = await msg.channel.fetch_message(msg.reference.message_id)
            if ref:
                cwm.add_reply(
                    message_id = ref.id,
                    author = self.minecraft_username(ref.author),
                    content = ref.content
                )
                
        CWCore.chat_passthrough(cwm)
        
    def minecraft_username(self, author):
        # user = UserManager(discord=author.id)
        # if user.is_valid():
        #     return get_mc_username(user.get()['minecraft'])
        # return f"{author.display_name}⚠"
        return f"{author.display_name}"
        
    def discord_username(self, author):
        # user = UserManager(minecraft=author['uuid'])
        # if user.is_valid():
        #     _id = user.get()['discord']
        #     username = self.bot.get_user(_id).display_name
        #     if not username:
        #         return f"{author['name']}❓"
        #     return username
        
        # return f"{author['name']}⚠️"
        return author['name']
    
    def is_staff(self, author):
        user = UserManager(minecraft=author["uuid"])
        if not user.is_valid():
            return False
        
        member = self.bot.get_guild(Config.get("WHITELIST.MONITOR.GUILD")).get_member(user.get()["discord"])
        if not member:
            return False
        
        for role in member.roles:
            if role.id in Config.get("AUTOMOD.ADMINS"):
                return True
        return False
    
    def cmd_help(self, author, *args):
        out = []
        for cmd in self.commands:
            out.append(f"!{cmd.name} - {cmd.description}")
        
        return "Available Commands:\n" + "\n".join(out) if out else "No commands available"
        
    def cmd_seen(self, author, *args):
        if not args: return "Usage: !seen <player>"
        player = args[0]
        CommandLogger.warn(f"ChatLink: Seen command for {player}")
        
        user = UserManager(minecraft=get_mc_uuid(player))
        if not user.is_valid():
            return f"Player not found"
        
        seen = user.get_seen()
        if not seen.ok:
            return f"Error: {seen.error}"
        
        if seen.meta == -1:
            return "This player has never been seen"
        elif seen.meta == -2:
            return "This player is currently online"
        else:
            diff = time.time() - seen.meta
            return f"This player was last seen {parse_time(diff)} ago"
            
    def cmd_warn(self, author, *args):
        if len(args) < 2:
            return "Usage: !warn <player> <reason>"
        
        if not self.is_staff(author):
            return "Insufficient permissions"
        
        
        player = args[0]
        reason = " ".join(args[1:])
        CommandLogger.warn(f"ChatLink: Warn command for {player} with reason: {reason}")
        
        
        moderator = UserManager(minecraft=get_mc_uuid(author["uuid"]))
        user = UserManager(minecraft=get_mc_uuid(player))
        
        if not user.is_valid():
            return f"Player not found"
        
        mod = Bot.cogs.get("Moderation")
        if not mod:
            return "Moderation util is not loaded"
        
        mod.warn_queue.append({
            "user": user,
            "reason": reason,
            "moderator": moderator.get()["discord"]
        })
        return f"Issued a warning to {player}"
        
        
        
    def process_command(self, command, author):
        if not command: return
        if not command.startswith("!"): return
        
        if not Config.get("MODULES.CHATLINK"): return
        
        name, *args = command[1:].split(" ")
        name = name.lower()
        
        for cmd in self.commands:
            if cmd.name == name:
                CommandLogger.debug(f"{name}: {args}")
                r = cmd.func(author, *args)
                if r: return f"{name.capitalize()}: {r}"
                return
        
        return False
        
    def on_chat_message(self, data):
        """
        Handle chat messages from the Clockwork Core API.
        """
        if not self.channel: return
        if not Config.get("MODULES.CHATLINK"): return
        
        user = self.discord_username(data['author'])
        
        waypoint = WP_REGEX.match(data['content'])
        if waypoint:
            name, initial, x, y, z, color_id, disabled, type_id, dimension_id = waypoint.groups()
            dimension = "Overworld"
            if "end" in dimension_id.lower(): dimension = "End"
            elif "nether" in dimension_id.lower(): dimension = "Nether"
            
            self.queue.append(CLMessage(embed=Embed(
                title = f"[{initial}] {name}",
                description = f"**{user}** has shared a waypoint at `{x}, {y}, {z}` in The {dimension}",
                color = Colors.DEFAULT
            )))
            return
        
        if data["content"].startswith("!"):
            try:
                r = self.process_command(data["content"], data["author"])                
                if r == False:
                    CWCore.chat_passthrough(CWChatMessage(0, "ClockBot", "Unknown Command"))
                    return
                    
                CWCore.chat_passthrough(CWChatMessage(0, "ClockBot", str(r)))
                    
            except Exception as e:
                CommandLogger.error(f"ChatLink: Failed to process command {data['content']} from {data['author']['name']}: {e}")
                CWCore.chat_passthrough(CWChatMessage(0, "ClockBot", f"Unable to process command"))
                return
                
            if r != None: return 
        
        self.queue.append(CLMessage(f"**{user}:** {data['content']}"))
        
    def on_player_join(self, data):
        """
        Handle player join events from the Clockwork Core API.
        """
        if not self.channel: return
        if not Config.get("MODULES.CHATLINK"): return
        
        self.queue.append(CLMessage(embed=Embed(
            description = f"**{self.discord_username(data)}** has joined",
            color = Colors.OK
        )))
        
        user = UserManager(minecraft=data["uuid"])
        r = user.just_seen()
        if not r.ok and user.is_valid():
            CommandLogger.error(f"ChatLink: Failed to update user {user.get()['discord']} ({user.get()['minecraft']}) status: {r.error}")
        
    def on_player_leave(self, data):
        """
        Handle player leave events from the Clockwork Core API.
        """
        if not self.channel: return
        if not Config.get("MODULES.CHATLINK"): return
        
        self.queue.append(CLMessage(embed=Embed(
            description = f"**{self.discord_username(data)}** has left",
            color = Colors.ERROR
        )))
        
        user = UserManager(minecraft=data["uuid"])
        r = user.just_seen()
        if not r.ok and user.is_valid():
            CommandLogger.error(f"ChatLink: Failed to update user {user.get()['discord']} ({user.get()['minecraft']}) status: {r.error}")
        
    def on_conn_open(self):
        """
        Handle connection open events from the Clockwork Core API.
        """
        if not self.channel: return
        if not Config.get("MODULES.CHATLINK"): return
        
        self.queue.append(CLMessage(embed=Embed(
            description = f"⚙️ Connected to Clockwork Core API",
            color = Colors.OK
        )))
        
    def on_conn_close(self, data):
        """
        Handle connection close events from the Clockwork Core API.
        """
        if not self.channel: return
        if not Config.get("MODULES.CHATLINK"): return
        
        self.queue.append(CLMessage(embed=Embed(
            description = f"⚠️ Disconnected from Clockwork Core API",
            color = Colors.ERROR
        )))
