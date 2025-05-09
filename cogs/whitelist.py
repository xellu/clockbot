import discord
from discord.ext import commands, tasks
from discord import app_commands, Embed
from enum import Enum
import time

from mdbb import Config, Bot, Colors, CommandLogger, DB

from core.templates.UserTemplate import UserTemplate, ApplicationTemplate, WLStatus, ActionTemplate
from core.templates.Messages import apply_for_whitelist_msg
from core.utils import get_mc_username, get_mc_uuid, random_str
from core.users import UserManager

from plugins.cwcore import CWCore, CWChatMessage

class PhantomUser:
    def __init__(self, _id: int):
        self.id = _id
        self.name = str(_id)

class Whitelist(commands.Cog):
    def __init__(self):
        self.bot = Bot
        
        self.guild = self.bot.get_guild(Config.get("WHITELIST.MONITOR.GUILD"))
        self.announce_channel = self.bot.get_channel(Config.get("WHITELIST.ANNOUNCE.CHANNEL"))
        self.admin_channel = self.bot.get_channel(Config.get("WHITELIST.ADMIN.CHANNEL"))
        self.membership_role = self.guild.get_role(Config.get("WHITELIST.MEMBERSHIP.ROLE")) if self.guild else None

        self.player_queue = []
   
        self.enabled = Config.get("MODULES.WHITELIST")
        if not self.enabled: return
        
        #checks------------
        if not self.guild:
            CommandLogger.error("Whitelist: Guild not found, please check your config")
            self.enabled = False
            
        if not self.announce_channel:
            CommandLogger.error("Whitelist: Announce channel not found, please check your config")
            self.enabled = False
            
        if not self.admin_channel:
            CommandLogger.error("Whitelist: Admin channel not found, please check your config")
            self.enabled = False
            
        if not self.membership_role:
            CommandLogger.error("Whitelist: Membership role not found, please check your config")
            self.enabled = False
            
        if not self.enabled:
            CommandLogger.error("Whitelist: Module disabled due to misconfigurations")
            return
        
        #---------
        
        self.update_members.start()
        CWCore.event.register("player.join", self.on_player_join)
    
    #TEMPORARY CODE / USED FOR MIGRATION ONLY--------------------------------------        
    def on_player_join(self, data): #send migration notice to the player
        if not self.enabled: return
        
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
        
        if data["name"] != "Xelluu": return
        
        CWCore.send_migration_notice(
            uuid = data["uuid"],
            username = data["name"],
            code = code
        )
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
                #TODO: await self.announce_delist(member, "Database mismatch")
                CommandLogger.warn(f"Whitelist: {member.name} is not whitelisted")
        
        for user in DB.get("clockbot").users.find({"discord": {"$nin": processed}}): #delete users that left the server
            user = UserManager(discord=user["discord"])
            discord_user = await self.bot.fetch_user(user.get()['discord'])
            if not discord_user:
                discord_user = PhantomUser(user.get()['discord'])

            await self.suggest_delist(discord_user, "User left the server")          
        
    async def suggest_delist(self, user: discord.User | PhantomUser, reason: str = None):
        if not self.enabled: return
        if not self.admin_channel: return
        if not user: return
        
        if DB.get("clockbot").actions.find_one({"user": user.id, "type": "wl-remove"}): #already suggested
            return
        
        if not reason:
            reason = "No reason provided"
            
        action_id = f"WLRS-{random_str(8)}"
        embed = Embed(
            title = "Whitelist Removal Suggestion",
            description = f"🚫 **{user.name}** should be removed from the whitelist\n> `{reason}`",
            color = Colors.ERROR
        )
        embed.set_author(name=user.name, icon_url=user.display_avatar.url if not isinstance(user, PhantomUser) else None)
        
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Approve", style=discord.ButtonStyle.success, custom_id="ok"))
        view.add_item(discord.ui.Button(label="Deny", style=discord.ButtonStyle.danger, custom_id="cancel"))
        
        msg = await self.admin_channel.send(embed=embed, view=view)
        
        #create an action report
        action = ActionTemplate()
        action["id"] = action_id
        action["msg"] = msg.id
        
        action["type"] = "wl-remove"
        action["user"] = user.id
        action["reason"] = reason
        
        DB.get("clockbot").actions.insert_one(action)
        
    async def announce_delist(self, user: dict, reason: str = None):
        if not self.enabled: return
        if not self.announce_channel: return
        
        if not reason:
            reason = "No reason provided"
            
        embed = Embed(
            description = f"🚫 {get_mc_username(user['minecraft'])} (<@{user['discord']}>) was removed from the whitelist:\n> `{reason}`",
            color = Colors.ERROR
        )
        await self.announce_channel.send(embed=embed)
        
    async def announce_whitelist(self, user: discord.Member, moderator: str):
        if not self.enabled: return
        if not self.announce_channel: return
        
        _user = UserManager(discord=user.id)
        embed = Embed(
            description = f"✅ {get_mc_username(_user.get()['minecraft'])} (<@{user.id}>) was whitelisted by <@{moderator}>",
            color = Colors.OK
        )
        await self.announce_channel.send(user.mention, embed=embed)
        
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not self.enabled: return
        
        msg = interaction.message
        approved = interaction.data.get("custom_id") == "ok" 
        
        if not msg: return
                
        action = DB.get("clockbot").actions.find_one({"msg": msg.id})
        if not action: return
        
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        if not approved:
            DB.get("clockbot").actions.delete_one({"msg": msg.id})
            await msg.delete()
            await interaction.response.send_message(embed=Embed(
                description = "✅ Action cancelled",
                color = Colors.OK
            ), ephemeral=True)
            
            return
        
        #approve action
        match action["type"]:
            case "wl-remove":
                user = UserManager(discord=action["user"])
                if not user.is_valid():
                    await interaction.followup.send(embed=Embed(
                        description = "🚫 User not found",
                        color = Colors.ERROR
                    ), ephemeral=True)
                    await msg.delete()
                    return
                
                user_data = user.user
                
                user.delete()                
                await self.announce_delist(user_data, action["reason"])
                              
                await interaction.followup.send(embed=Embed(
                    description = f"✅ {get_mc_username(user_data['minecraft'])} was removed from whitelist:\n> `{action['reason']}`",
                    color = Colors.OK
                ), ephemeral=True)
                
                await msg.delete()
                  
            case "wl-add":
                pass
        
                