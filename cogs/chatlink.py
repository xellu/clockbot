from discord.ext import commands, tasks
from discord import app_commands, Embed
import json
import time

from mdbb import Bot, Config, CommandLogger, Colors, DB
from core.utils import get_mc_username, get_mc_uuid, random_str
from core.templates.Messages import migration_notice
from core.users import UserManager

from plugins.cwcore import CWCore, CWChatMessage


class CLMessage:
    def __init__(self, content=None, embed = None):
        self.content = content
        self.embed = embed

class ChatLink(commands.Cog):
    def __init__(self):
        self.bot = Bot
        self.channel = self.bot.get_channel(Config.get("CHATLINK.CHANNEL"))
        
        if not Config.get("MODULES.CHATLINK"): return
        if not self.channel:
            CommandLogger.error("ChatLink: Channel not found, please check your config")
        
        self.queue = []
        self.queue_loop.start()
        
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
        
    def on_chat_message(self, data):
        """
        Handle chat messages from the Clockwork Core API.
        """
        if not self.channel: return
        if not Config.get("MODULES.CHATLINK"): return
        
        self.queue.append(CLMessage(f"**{data['author']['name']}:** {data['content']}"))
        
    def on_player_join(self, data):
        """
        Handle player join events from the Clockwork Core API.
        """
        if not self.channel: return
        if not Config.get("MODULES.CHATLINK"): return
        
        self.queue.append(CLMessage(embed=Embed(
            description = f"**{data['name']}** has joined",
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
            description = f"**{data['name']}** has left",
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
