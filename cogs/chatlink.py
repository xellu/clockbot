from discord.ext import commands, tasks
from discord import app_commands, Embed
import json

from mdbb import Bot, Config, CommandLogger, Colors
from plugins.puffer import Puffer

class ChatLink(commands.Cog):
    def __init__(self):
        self.bot = Bot
        self.channel = self.bot.get_channel(Config.get("CHATLINK.CHANNEL"))
        
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
        
        
        #example command
        #/tellraw @a ["",{"text":"[Discord]","color":"#358BFF"},{"text":" Username:","color":"#77C2FF"},{"text":" hello world!! "},{"text":"[attachment]","color":"yellow","clickEvent":{"action":"open_url","value":"https://map.troll.ink/"}}]
        #data:
        # [
        #     {
        #         "color": "#358BFF",
        #         "text": "[Discord]"
        #     },
        #     {
        #         "color": "#77C2FF",
        #         "text": " Username:"
        #     },
        #     {
        #         "text": " hello world!! "
        #     },
        #-------- attachments
        #     {
        #         "clickEvent": {
        #             "action": "open_url",
        #             "value": "https://map.troll.ink/"
        #         },
        #         "color": "yellow",
        #         "text": "[attachment]"
        #     }
        # ]
        
        content = [
            {
                "color": "#358BFF",
                "text": "[Discord]"
            },
            {
                "color": "#77C2FF",
                "text": f" {msg.author.display_name}:"
            },
            {
                "color": "#FFFFFF",
                "text": f" {msg.content} "
            }
        ]
        
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