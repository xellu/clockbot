from discord.ext import commands, tasks
from discord import app_commands, Embed
import json
import time
import re

from mdbb import Bot, Config, CommandLogger, Colors, DB
from core.utils import get_mc_username, get_mc_uuid, random_str, parse_time, escape_md
from core.users import UserManager

from plugins.cwcore import CWCore, CWChatMessage

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
            CLCommand("seen", "Check when was a player last seen", [CLCArgs("player")], self.cmd_seen),
        }
        
        CWCore.event.register("chat.message", self.on_chat_message)
        CWCore.event.register("player.join", self.on_player_join)
        CWCore.event.register("player.leave", self.on_player_leave)
        CWCore.event.register("conn.open", self.on_conn_open)
        CWCore.event.register("conn.drop", self.on_conn_close)
        
    @tasks.loop(seconds=1)
    async def queue_loop(self):
        buffer = []
        for msg in self.queue:            
            if msg.embed:
                if buffer:
                    await self.channel.send("\n".join(buffer))
                    buffer = []
                await self.channel.send(embed=msg.embed)
            else:
                buffer.append(msg.content.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere"))
                
        self.queue.clear()
                
        if not buffer: return
        await self.channel.send("\n".join(buffer))
        
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
            author = msg.author.display_name,
            content = msg.content,
            attachments = [attachment.url for attachment in msg.attachments],
        )
        if msg.reference:
            ref = await msg.channel.fetch_message(msg.reference.message_id)
            if ref:
                cwm.add_reply(
                    message_id = ref.id,
                    author = ref.author.display_name,
                    content = ref.content
                )
                
        CWCore.chat_passthrough(cwm)
        
    def cmd_seen(self, *args):
        if not args: return "No player specified"
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
            
        
        
    def process_command(self, command, author):
        if not command: return
        if not command.startswith("!"): return
        
        if not Config.get("MODULES.CHATLINK"): return
        
        name, *args = command[1:].split(" ")
        name = name.lower()
        
        for cmd in self.commands:
            if cmd.name == name:
                CommandLogger.warn(f"{name}: {args}")
                r = cmd.func(*args)
                if r: return f"{name.capitalize()}: {r}"
                return
        
        return False
        
    def on_chat_message(self, data):
        """
        Handle chat messages from the Clockwork Core API.
        """
        if not self.channel: return
        if not Config.get("MODULES.CHATLINK"): return
        
        waypoint = WP_REGEX.match(data['content'])
        if waypoint:
            name, initial, x, y, z, color_id, disabled, type_id, dimension_id = waypoint.groups()
            dimension = "Overworld"
            if "end" in dimension_id.lower(): dimension = "End"
            elif "nether" in dimension_id.lower(): dimension = "Nether"
            
            self.queue.append(CLMessage(embed=Embed(
                title = f"[{initial}] {name}",
                description = f"**{escape_md(data['author']['name'])}** has shared a waypoint at `{x}, {y}, {z}` in The {dimension}",
                color = Colors.DEFAULT
            )))
            return
        
        if data["content"].startswith("!"):
            try:
                r = self.process_command(data["content"], data["author"]["name"])                
                if r == False:
                    CWCore.chat_passthrough(CWChatMessage(0, "ClockBot", "Unknown Command"))
                    return
                    
                CWCore.chat_passthrough(CWChatMessage(0, "ClockBot", str(r)))
                    
            except Exception as e:
                CommandLogger.error(f"ChatLink: Failed to process command {data['content']} from {data['author']['name']}: {e}")
                CWCore.chat_passthrough(CWChatMessage(0, "ClockBot", f"Unable to process command"))
                return
                
            if r != None: return 
        
        self.queue.append(CLMessage(f"**{escape_md(data['author']['name'])}:** {data['content']}"))
        
    def on_player_join(self, data):
        """
        Handle player join events from the Clockwork Core API.
        """
        if not self.channel: return
        if not Config.get("MODULES.CHATLINK"): return
        
        self.queue.append(CLMessage(embed=Embed(
            description = f"**{escape_md(data['name'])}** has joined",
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
            description = f"**{escape_md(data['name'])}** has left",
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
