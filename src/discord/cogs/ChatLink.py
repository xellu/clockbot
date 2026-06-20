import re
import discord
from discord import Embed
from discord.ext import commands

from src.lib.Discord import Bot, AddCog
from src.lib.Colors import *
from src.lib.Mongo import Mongo
from src.lib.User import UserManager
from src.lib.Clockwork import CW

from nautica import Services, Config
from plugins.Clockwork import Clockwork, CWChatMessage
from plugins.CWEvents import ChatMessageEvent, PlayerJoinEvent, PlayerLeaveEvent

WP_REGEX = re.compile(r"xaero-waypoint:(.+?):(.+?):(.+?):(.+?):(.+?):(.+?):(.+?):(.+?):(.+)")

class ChatLink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self._inGameChannel = None
        
        CW.onChatMessage()(self.on_chat_message)
        CW.onPlayerJoin()(self.on_player_join)
        CW.onPlayerLeave()(self.on_player_leave)

    async def inGameChannel(self) -> discord.TextChannel:
        if self._inGameChannel is None:
            c = await Bot.fetch_channel(Config("clockbot")["chatlink.channelId"])
            self._inGameChannel = c
            return c
        
        return self._inGameChannel
        
    async def on_chat_message(self, event: ChatMessageEvent):
        # Logger.ok(event.author.name)
        channel = await self.inGameChannel()
        
        waypoint = WP_REGEX.match(event.content)
        if waypoint:
            name, initial, x, y, z, color_id, disabled, type_id, dimension_id = waypoint.groups()
            dimension = "Overworld"
            if "end" in dimension_id.lower(): dimension = "End"
            elif "nether" in dimension_id.lower(): dimension = "Nether"
            
            await channel.send(embed=Embed(
                title = f"[{initial}] {name}",
                description = f"**{event.author.name_escaped}** has shared a waypoint at `{x}, {y}, {z}` in The {dimension}",
                color = INFO
            ))
            return
        
        await channel.send(f"**{event.author.name_escaped}:** {event.content}")
        Mongo("mc_events").insert_one({
            "type": "message",
            "player": event.author.uuid,
            "content": event.content
        })
        
    async def on_player_join(self, event: PlayerJoinEvent):
        channel = await self.inGameChannel()
        u = UserManager(minecraft=event.player.uuid)
        if u.is_valid(): u.just_seen()
        
        
        await channel.send(embed=Embed(
            description = f"**{event.player.name_escaped}** has joined",
            color = OK
        ))
        
        Mongo("mc_events").insert_one({
            "type": "join",
            "player": event.player.uuid
        })
        
    async def on_player_leave(self, event: PlayerLeaveEvent):
        channel = await self.inGameChannel()
        
        await channel.send(embed=Embed(
            description = f"**{event.player.name_escaped}** has left",
            color = ERROR
        ))
        
        Mongo("mc_events").insert_one({
            "type": "leave",
            "player": event.player.uuid
        })
        
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot: return
        if msg.channel.id != Config("clockbot")["chatlink.channelId"]:
            return
        
        m = CWChatMessage(
            message_id = msg.id,
            author = msg.author.display_name,
            content = msg.content,
            attachments = [attachment.url for attachment in msg.attachments],
        )
        if msg.reference:
            ref = await msg.channel.fetch_message(msg.reference.message_id)
            if ref:
                m.add_reply(
                    message_id = ref.id,
                    author = ref.author.display_name,
                    content = ref.content
                )
        
        mj = m.toJson()
        mj["member"] = msg.author.id
        if m.reply:
            mj["reply"]["author"] = ref.author.id
        
        CW.SendChatMessage(m)
        Mongo("dc_events").insert_one({
            "type": "message",
            **mj
        })
        
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        Mongo("dc_events").insert_one({
            "type": "join",
            "member": member.id
        })
        
    @commands.Cog.listener()
    async def on_member_leave(self, member: discord.Member):
        Mongo("dc_events").insert_one({
            "type": "leave",
            "member": member.id
        })
    
        
AddCog(ChatLink)