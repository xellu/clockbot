import discord
from discord.ext import commands, tasks
from discord import app_commands, Embed
from enum import Enum
import time

from mdbb import Config, Bot, Colors, CommandLogger, DB

from core.templates.UserTemplate import UserTemplate, ApplicationTemplate, WLStatus
from core.templates.Messages import apply_for_whitelist_msg
from core.utils import get_mc_username, get_mc_uuid, random_str
from core.users import UserManager

from plugins.cwcore import CWCore, CWChatMessage

class PhantomUser:
    def __init__(self, name: str):
        self.name = name

class Whitelist(commands.Cog):
    def __init__(self):
        self.bot = Bot
        
        self.guild = self.bot.get_guild(Config.get("WHITELIST.MONITOR.GUILD"))
        self.log_channel = self.bot.get_channel(Config.get("WHITELIST.ANNOUNCE.CHANNEL"))
        self.membership_role = self.guild.get_role(Config.get("WHITELIST.MEMBERSHIP.ROLE")) if self.guild else None

        self.player_queue = []
   
        self.enabled = Config.get("MODULES.WHITELIST")
        if not self.enabled: return
        
        if not self.guild:
            CommandLogger.error("Whitelist: Guild not found, please check your config")
            self.enabled = False
            
        if not self.log_channel:
            CommandLogger.error("Whitelist: Log channel not found, please check your config")
            self.enabled = False
            
        if not self.membership_role:
            CommandLogger.error("Whitelist: Membership role not found, please check your config")
            self.enabled = False
            
        if not self.enabled:
            CommandLogger.error("Whitelist: Module disabled due to misconfigurations")
            return
        
        self.update_members.start()
        
        CWCore.event.register("player.join", self.on_player_join)
    
    #TEMPORARY CODE / USED FOR MIGRATION ONLY--------------------------------------        
    def on_player_join(self, data): #send migration notice to the player
        # CommandLogger.info(f"Whitelist: Player {data['name']} joined the server")
        user = UserManager(minecraft=data["uuid"])
        if user.is_valid():
            return
        
        if DB.get("clockbot").codes.find_one({"uuid": data["uuid"]}):
            code = DB.get("clockbot").codes.find_one({"uuid": data["uuid"]})["code"]
        else:
            code = random_str(5)
            DB.get("clockbot").codes.insert_one({
                "uuid": data["uuid"],
                "code": code
            })
        
        # CWCore.send_migration_notice(
        #     uuid = data["uuid"],
        #     username = data["name"],
        #     code = code
        # )
        CommandLogger.info(f"Unregistered player {data['name']} joined, sending migration notice")
    #-----------------------------------------------------------------------
        
    #sync member roles with whitelist status
    @tasks.loop(seconds=300)
    async def update_members(self):
        if not self.enabled: return
        
        processed = []
        for member in self.guild.members:
            if member.bot: continue
            processed.append(member.id)
            
            user = UserManager(discord=member.id)
            if not user.is_valid() and self.membership_role in member.roles: #handle users without a ClockAPI account
                # await member.remove_roles(self.membership_role)
                # await self.announce_delist(member, "No associated ClockAPI account found")
                # CommandLogger.error(f"Whitelist: {member.name} does not have a profile")
                #disabled for now, waiting for migration to end
                continue
            
            if not user.is_valid():
                continue
            
            if user.get()["whitelist"]["status"] == WLStatus.APPROVED.value and self.membership_role not in member.roles: #handle approved users without role
                await member.add_roles(self.membership_role)
                await self.announce_whitelist(member, user.get()["whitelist"]["moderator"])
                CommandLogger.ok(f"Whitelist: {member.name} is whitelisted")
                
            if user.get()["whitelist"]["status"] != WLStatus.APPROVED.value and self.membership_role in member.roles: #handle rejected users with role
                await member.remove_roles(self.membership_role)
                await self.announce_delist(member, "Database mismatch")
                CommandLogger.warn(f"Whitelist: {member.name} is not whitelisted")
            
        
        for user in DB.get("clockbot").users.find({"discord": {"$nin": processed}}): #delete users that left the server
            user = UserManager(discord=user["discord"])
            discord_user = await self.bot.fetch_user(user.get()['discord'])
            if not discord_user:
                discord_user = PhantomUser(user.get()['discord'])

            # user.delete()
            await self.announce_delist(discord_user, "Left the discord server", deleted=True)
            
            CommandLogger.error(f"Whitelist: {user.get()['discord']} {discord_user} is not in the guild")
    
    #Whitelist de-listing
    async def announce_delist(self, member: discord.Member, reason=None, deleted=False):
        embed = Embed(
            description = f"👋 **@{member.name}** has been de-listed: `{reason or 'Unspecified'}`",
            color = Colors.ERROR
        )
        embed.set_author(name=member.name, icon_url=member.display_avatar.url if not isinstance(member, PhantomUser) else None)
        if deleted:
            embed.set_footer(text="This profile has been deleted permanently")
        await self.log_channel.send(embed=embed)
    
    #Whitelist apply reject
    async def announce_reject(self, member: discord.Member, reason=None):
        embed = Embed(
            description = f"❌ **@{member.name}**'s application was rejected: `{reason or 'Unspecified'}`",
            color = Colors.ERROR
        )
        embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        await self.log_channel.send(embed=embed)
    
    #Whitelist apply approve
    async def announce_whitelist(self, member: discord.Member, moderator: int):
        embed = Embed(
            description = f"✅ **@{member.name}** has been whitelisted by <@{moderator}>",
            color = Colors.OK
        )
        embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        await self.log_channel.send(embed=embed)
    
   