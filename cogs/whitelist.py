import discord
from discord.ext import commands, tasks
from discord import app_commands, Embed
from enum import Enum
import time

from mdbb import Config, Bot, Colors, CommandLogger, DB

from core.templates.UserTemplate import UserTemplate, WLStatus, ActionTemplate, WLKeyNames
from core.utils import get_mc_username, get_mc_uuid, random_str, escape_md
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
        if not self.enabled:
            CommandLogger.warning("Module disabled: Whitelist")
            return
        
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
        self.check_for_whitelists.start()
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
        
        # if data["name"] != "Xelluu": return
        
        CWCore.send_migration_notice(
            uuid = data["uuid"],
            username = data["name"],
            code = code
        )
        CommandLogger.info(f"Unregistered player {data['name']} joined, sending migration notice")
    #-----------------------------------------------------------------------
        
    # get new whitelist applications
    @tasks.loop(seconds=60)
    async def check_for_whitelists(self):
        if not self.enabled: return
        
        applications = DB.get("clockbot").whitelist.find({})
        for app in applications:
            username = get_mc_username(app["minecraft"])
            if not app.get("minecraft") or not username:
                CommandLogger.error(f"Whitelist: Invalid UUID {app['minecraft']}")
                DB.get("clockbot").whitelist.delete_one({"_id": app["_id"]})
                continue
            
            user = UserManager(
                discord = app["discord"],
            )
            
            if (user.is_valid() or UserManager(minecraft=username).is_valid()) and user.get()["whitelist"]["status"] in [WLStatus.PENDING.value, WLStatus.APPROVED.value]:
                CommandLogger.error(f"Whitelist: User {user.get()['minecraft']} already exists")
                DB.get("clockbot").whitelist.delete_one({"_id": app["_id"]})
                continue
            
            if user.is_valid() and user.get()["whitelist"]["status"] == WLStatus.REJECTED.value and time.time() < user.get()["whitelist"]["reapply_in"]:
                CommandLogger.error(f"Whitelist: User {user.get()['minecraft']} is not allowed to reapply")
                continue
            
            if not user.is_valid():
                user.create(
                    discord = app["discord"],
                    minecraft = username
                )
                
                user.user["whitelist"]["status"] = WLStatus.PENDING.value
                user.user["whitelist"]["moderator"] = None
                user.user["whitelist"]["reapply_in"] = None
                user.user["whitelist"]["reason"] = None
                user.user["whitelist"]["answers"] = app["answers"]
                user.update()
                
            embed = Embed(
                title = "Whitelist Application",
                description = f"**{escape_md(username)}** (<@{app['discord']}>) has applied for whitelist",
                color = Colors.OK
            )
            for key, value in app["answers"].items():
                if isinstance(value, list):
                    value = ", ".join(value) if value else "N/A"
                if value is None:
                    value = "N/A"
                               
                embed.add_field(name=WLKeyNames.get(key, key), value=f"`{value}`", inline=False)
                
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Approve", style=discord.ButtonStyle.success, custom_id="ok"))
            
            select = discord.ui.Select(placeholder="Reject for", custom_id="ok-reject")
            select.add_option(label="Underage", value="Underage")
            select.add_option(label="Inappropriate content", value="Inappropriate content")
            select.add_option(label="Not enough information", value="Not enough information")
            select.add_option(label="Other", value="Other")
            
            view.add_item(select)
            
            msg = await self.admin_channel.send(embed=embed, view=view)
            action = ActionTemplate()
            action["id"] = f"WLAP-{random_str(8)}"
            action["msg"] = msg.id
            action["type"] = "wl-add"
            action["user"] = app["discord"]
            
            DB.get("clockbot").actions.insert_one(action)
            DB.get("clockbot").whitelist.delete_one({"_id": app["_id"]})
        
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
            try:
                discord_user = await self.bot.fetch_user(user.get()['discord'])
            except:
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
            description = f"🚫 {escape_md(get_mc_username(user['minecraft']))} (<@{user['discord']}>) was removed from the whitelist:\n> `{reason}`",
            color = Colors.ERROR
        )
        await self.announce_channel.send(embed=embed)
        
    async def announce_whitelist(self, user: discord.Member, moderator: str):
        if not self.enabled: return
        if not self.announce_channel: return
        
        _user = UserManager(discord=user.id)
        embed = Embed(
            description = f"✅ {escape_md(get_mc_username(_user.get()['minecraft']))} (<@{user.id}>) was whitelisted by <@{moderator}>",
            color = Colors.OK
        )
        await self.announce_channel.send(user.mention, embed=embed)
        
    async def announce_reject(self, user: UserManager, reason: str = None):
        if not self.enabled: return
        if not self.announce_channel: return
        
        embed = Embed(
            description = f"🚫 {escape_md(get_mc_username(user.get()['minecraft']))} (<@{user.get()['discord']}>) was rejected for `{reason}`, you can reapply <t:{int(user.user['whitelist']['reapply_in'])}:R>",
            color = Colors.ERROR
        )
        await self.announce_channel.send(f"<@{user.get()['discord']}>", embed=embed)
        
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not self.enabled: return
        
        msg = interaction.message
        approved = interaction.data.get("custom_id") in ["ok", "ok-reject"]
        
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
                    description = f"✅ {escape_md(get_mc_username(user_data['minecraft']))} was removed from whitelist:\n> `{action['reason']}`",
                    color = Colors.OK
                ), ephemeral=True)
                
                await msg.delete()
                  
            case "wl-add":
                user = UserManager(discord=action["user"])
                if not user.is_valid():
                    await interaction.followup.send(embed=Embed(
                        description = "🚫 User not found",
                        color = Colors.ERROR
                    ), ephemeral=True)
                    await msg.delete()
                    return
                
                if interaction.data.get("custom_id") == "ok-reject":
                    user.user["whitelist"]["status"] = WLStatus.REJECTED.value
                    user.user["whitelist"]["moderator"] = interaction.user.id
                    user.user["whitelist"]["reapply_in"] = time.time() + 604800
                    user.user["whitelist"]["reason"] = interaction.data.get("values")[0]
                    user.update()
                    
                    await interaction.followup.send(embed=Embed(
                        description = f"✅ {escape_md(get_mc_username(user.get()['minecraft']))} was rejected for:\n> `{interaction.data.get('values')[0]}`",
                        color = Colors.OK
                    ), ephemeral=True)
                    await msg.delete()
                    await self.announce_reject(user, interaction.data.get("values")[0])
                    
                    return
                
                user.user["whitelist"]["status"] = WLStatus.APPROVED.value
                user.user["whitelist"]["moderator"] = interaction.user.id
                user.user["whitelist"]["reapply_in"] = None
                user.user["whitelist"]["reason"] = None
                user.update()
                
                await interaction.followup.send(embed=Embed(
                    description = f"✅ {escape_md(get_mc_username(user.get()['minecraft']))} was whitelisted",
                    color = Colors.OK
                ), ephemeral=True)
                await msg.delete()
                
                member = await self.guild.fetch_member(user.get()["discord"])
                member.add_roles(self.membership_role)
                await self.announce_whitelist(member, user.get()["whitelist"]["moderator"])
                