from discord.ext import commands, tasks
from discord import app_commands, Embed
import json
import time

from mdbb import Bot, Config, CommandLogger, Colors, DB
from core.utils import get_mc_username, get_mc_uuid, random_str
from core.templates.Messages import migration_notice

from plugins.puffer import Puffer

class ChatLink(commands.Cog):
    def __init__(self):
        self.bot = Bot
        self.channel = self.bot.get_channel(Config.get("CHATLINK.CHANNEL"))
        
        if not Config.get("MODULES.CHATLINK"): return
        self.check_chatlink.start()
        
    def bold_username(self, name):
        username = ""
        if " " in name:
            temp = name.split(" ")
            for i in range(len(temp)):
                if i == len(temp)-1:
                    username += f"**{temp[i]}:**"
                else:
                    username += f"{temp[i]} "
        else:
            username = f"**{name}:**"
        return username
        
    @tasks.loop(seconds=1)
    async def check_chatlink(self):
        if not Puffer.chat_messages:
            return
        
        content = ""
        for msg in Puffer.chat_messages:
            if msg["type"] == "chat":
                username = self.bold_username(msg["username"])
                    
                content += f"{username} {msg['message']}\n"
                Puffer.chat_messages.remove(msg)
                
        if content:
            await self.channel.send(content.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere"))
            
        for msg in Puffer.chat_messages:
            if msg["type"] in ["join", "leave"]:
                if msg["type"] == "join": await self.on_join(msg["username"])
                embed = Embed(
                    description = f"{msg['username']} has joined the server." if msg["type"] == "join" else f"{msg['username']} has left the server.",
                    color = Colors.OK if msg["type"] == "join" else Colors.ERROR
                )
                await self.channel.send(embed=embed)
                Puffer.chat_messages.remove(msg)
            
        for msg in Puffer.chat_messages:
            if msg["type"] == "waypoint":
                embed = Embed(
                    title = f'[{msg["initial"]}] {msg["name"]}',
                    description=f"{self.bold_username(msg['username'])} has shared a waypoint.",
                    color = Colors.DEFAULT
                )
                embed.set_author(name="Waypoint")
                embed.add_field(
                    name = "Location",
                    value = f"**X:** {msg['x']} **Y:** {msg['y']} **Z:** {msg['z']} `{'Nether' if 'nether' in msg['dimension_id'].lower() else ('End' if 'end' in msg['dimension_id'].lower() else 'Overworld')}`",    
                )
                
                await self.channel.send(embed=embed)
                Puffer.chat_messages.remove(msg)
            
    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return
        
        if msg.channel.id != Config.get("CHATLINK.CHANNEL"):
            return
        
        
        content = []
        
        if msg.reference:
            reply_msg = await msg.channel.fetch_message(msg.reference.message_id)
            text = f"{reply_msg.author.display_name}: {reply_msg.content}" if reply_msg.content else f"Replying to {reply_msg.author.display_name}"
            text = f"{text[:97]}..." if len(text) > 100 else text
            text = Puffer.fix_username_reverse(text)
            
            content.append({
                "color": "#358BFF",
                "text": "[Discord]"
            })
            content.append({
                "color": "#B3B3B3",
                "text": f" ⬊ {text}\n"
            })
    
        content += [{
                "color": "#358BFF",
                "text": "[Discord]"
            },
            {
                "color": "#77C2FF",
                "text": f" {msg.author.display_name}:"
            },
            {
                "color": "#FFFFFF",
                "text": f" {msg.content} " if msg.content else " "
        }]
        
        if msg.attachments:
            for i, attachment in enumerate(msg.attachments):
                content.append({
                    "clickEvent": {
                        "action": "open_url",
                        "value": attachment.url
                    },
                    "color": "yellow",
                    "text": f"[Attachment {i+1}]"
                })
                
        Puffer.execute_command(f"/tellraw @a {json.dumps(content)}")
        
    async def on_join(self, username):
        username = username.split(" ")[len(username.split(" ")) - 1]
        uuid = get_mc_uuid(username)
        if not uuid:
            return CommandLogger.warn(f"Failed to get UUID for {username}")
        
        user = DB.get("clockbot").users.find_one({"minecraft": uuid})
        if user and user["minecraft"]:
            #update user's last seen time
            CommandLogger.info(f"User {username} ({uuid}) has joined the server, updating last seen time.")
            DB.get("clockbot").users.update_one({"minecraft": uuid}, {"$set": {"last_seen": time.time()}})
            return
       
        #handle user linking here
        code = DB.get("clockbot").codes.find_one({"uuid": uuid})
        if code is None:
            code = random_str(5)
            DB.get("clockbot").codes.insert_one({
                "uuid": uuid,
                "code": code
            })
        else:
            code = code["code"]
            
        link_message = migration_notice(code)
        
        CommandLogger.warn(f"User {username} ({uuid}) has joined the server and is not linked. Sending migration notice.")
        if username != "Xelluu": return
        
        Puffer.execute_command(f"/tellraw {username} {json.dumps(link_message)}")