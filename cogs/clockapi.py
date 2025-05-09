import discord
from discord.ext import commands
from discord import app_commands, Embed
from enum import Enum

from mdbb import Bot, Config, CommandLogger, Colors, DB

from core.config import ConfigManager
from core.templates.UserTemplate import UserTemplate, WLStatus
from core.utils import get_mc_username, get_mc_uuid
from core.users import UserManager

from plugins.cwcore import CWCore

class AccountManagerActions(Enum):
    Link = "Link"
    Unlink = "Unlink"
    Relink = "Relink"
    
    Create = "Create"
    Delete = "Delete"
    
class ClockAPI(commands.Cog):
    def __init__(self):
        self.bot = Bot

    #TEMPORARY CODE / USED FOR MIGRATION ONLY--------------------------------------        
    @app_commands.command(name="migrate", description="Add your Minecraft and Discord accounts to ClockAPI")
    @app_commands.describe(code="The code you received")
    async def migrate_to_clockapi(self, ctx, code: str):
        await ctx.response.defer(ephemeral=True)
        
        user = UserManager(discord=ctx.user.id)
        if user.is_valid() and user.get()["minecraft"]:
            await ctx.response.send_message(embed=Embed(description="You already have a ClockAPI profile", color=Colors.ERROR), ephemeral=True)
            return
        
        code = DB.get("clockbot").codes.find_one({"code": code})
        if code is None:
            await ctx.response.send_message(embed=Embed(description="Invalid code.", color=Colors.ERROR), ephemeral=True)
            return
        
        r = user.create(minecraft=get_mc_username(code["uuid"]))
        if not r.ok:
            await ctx.response.send_message(embed=Embed(description=r.error, color=Colors.ERROR), ephemeral=True)
            return
        
        user.user["whitelist"]["status"] = WLStatus.APPROVED.value
        user.user["whitelist"]["moderator"] = self.bot.user.id
        user.update()
        
        DB.get("clockbot").codes.delete_one({"code": code["code"]})
        
        await ctx.followup.send(embed=Embed(
            title = "Thank you for migrating!",
            description = f"We've created your ClockAPI profile!",
            color = Colors.OK
        ), ephemeral=True)
    #--------------------------------------------------------------------------------------
        
    @app_commands.command(name="profile", description="View your ClockAPI profile")
    async def profile(self, ctx):
        user = UserManager(discord=ctx.user.id)
        if not user.is_valid():
            await ctx.response.send_message(embed=Embed(description="You do not have a ClockAPI profile.", color=Colors.ERROR), ephemeral=True)
            return
        
        await ctx.response.defer(ephemeral=True)
        
        mc_username = get_mc_username(user.get()["minecraft"])
        
        seen = user.get_seen(md=True)
        embed = Embed(
            title = "Your Profile",
            description = f"""
**Minecraft:** {mc_username or ''} `{user.get()['minecraft'] or 'NOT LINKED'}`
**Discord:** <@{user.get()['discord']}> `{user.get()['discord']}`

**Last Seen:** {seen.meta if seen.ok else seen.error}
**Whitelist:** {user.get()['whitelist']["status"]}
            """,
            color = Colors.DEFAULT
        )
        
        embed.set_thumbnail(url=f"https://mc-heads.net/body/{user.get()['minecraft']}")
        
        await ctx.followup.send(embed=embed)
    
    @app_commands.command(name="seen", description="See when a user was last seen")
    @app_commands.describe(discord="Discord ID of the user", minecraft="Minecraft username")
    async def seen(self, ctx, discord: discord.User = None, minecraft: str = None):
        if not discord and not minecraft:
            await ctx.response.send_message(embed=Embed(description="Please provide either a Discord ID or a Minecraft username.", color=Colors.ERROR), ephemeral=True)
            return
        
        user = None
        if discord:
            user = UserManager(discord=discord.id)
        elif minecraft:
            user = UserManager(minecraft=get_mc_uuid(minecraft))
            
        if not user.is_valid():
            await ctx.response.send_message(embed=Embed(description="User does not have a ClockAPI profile.", color=Colors.ERROR), ephemeral=True)
            return
        
        mc_username = get_mc_username(user.get()["minecraft"])
        seen = user.get_seen(md=True)
        if not seen.ok:
            await ctx.response.send_message(embed=Embed(description=seen.error, color=Colors.ERROR), ephemeral=True)
            return

        last_seen = seen.meta        
        if seen.meta == "Never":
            last_seen = f"{mc_username} has never been seen"
        elif seen.meta == "Online":
            last_seen = f"{mc_username} is currently online"
            
        await ctx.response.send_message(embed=Embed(
            title = "Last Seen",
            description = last_seen,
            color = Colors.DEFAULT
        ), ephemeral=True)
        
    @app_commands.command(name="lookup", description="Lookup a user's profile")
    @app_commands.describe(discord="Discord ID of the user", minecraft="Minecraft username")
    async def lookup(self, ctx, discord: discord.User = None, minecraft: str = None):
        if not discord and not minecraft:
            await ctx.response.send_message(embed=Embed(description="Please provide either a Discord ID or a Minecraft username.", color=Colors.ERROR), ephemeral=True)
            return
        
        user = None
        if discord:
            user = UserManager(discord=discord.id)
        elif minecraft:
            user = UserManager(minecraft=get_mc_uuid(minecraft))
            
        if not user:
            await ctx.response.send_message(embed=Embed(description="User does not have a ClockAPI profile.", color=Colors.ERROR), ephemeral=True)
            return
        
        await ctx.response.send_message(embed=Embed(
            title = f"Lookup",
            description  = f"""
**Minecraft:** {get_mc_username(user.get()["minecraft"])} `{user.get()['minecraft']}`
**Discord:** <@{user.get()['discord']}> `{user.get()['discord']}`
**Last Seen:** {user.get_seen(md=True).meta}
            """,
            color = Colors.DEFAULT
        ).set_thumbnail(url=f"https://mc-heads.net/body/{user.get()['minecraft']}"), ephemeral=True)
        
    
    @app_commands.command(name="account", description="Manage user accounts. Users who are created will have automatically approved whitelists")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        user = "User to manage",
        action = "Action to perform",
        minecraft_username = "Minecraft username (used for: link, relink, create)"
    )
    async def account_manager(self, ctx,
        user: discord.User,
        action: AccountManagerActions,
        minecraft_username: str = None,
    ):
        user = UserManager(discord=user.id)

        match action:
            case AccountManagerActions.Unlink:
                uuid = user.get()['minecraft'] if user.is_valid() else None
                r = user.unlink()
                if not r.ok:
                    await ctx.response.send_message(embed=Embed(description=r.error, color=Colors.ERROR), ephemeral=True)
                    return
                
                await ctx.response.send_message(embed=Embed(
                    description = f"Unlinked the `{uuid}` Minecraft account from <@{user.get()['discord']}>'s profile",
                    color = Colors.OK
                ), ephemeral=True)
            
            case AccountManagerActions.Link:
                if not minecraft_username:
                    await ctx.response.send_message(embed=Embed(description="Please provide a Minecraft username.", color=Colors.ERROR), ephemeral=True)
                    return
                
                r = user.link(minecraft_username)
                if not r.ok:
                    await ctx.response.send_message(embed=Embed(description=r.error, color=Colors.ERROR), ephemeral=True)
                    return
                
                await ctx.response.send_message(embed=Embed(
                    description = f"Linked a Minecraft account {minecraft_username} `{user.get()['minecraft']}` to <@{user.get()['discord']}>'s profile",
                    color = Colors.OK
                ), ephemeral=True)
                
            case AccountManagerActions.Relink:
                if not minecraft_username:
                    await ctx.response.send_message(embed=Embed(description="Please provide a Minecraft username.", color=Colors.ERROR), ephemeral=True)
                    return
                
                r = user.relink(minecraft_username)
                if not r.ok:
                    await ctx.response.send_message(embed=Embed(description=r.error, color=Colors.ERROR), ephemeral=True)
                    return
                
                await ctx.response.send_message(embed=Embed(
                    description = f"Re-linked the Minecraft account `{minecraft_username}` to <@{user.get()['discord']}>'s profile",
                    color = Colors.OK
                ), ephemeral=True)
                
            case AccountManagerActions.Delete:
                r = user.delete()
                if not r.ok:
                    await ctx.response.send_message(embed=Embed(description=r.error, color=Colors.ERROR), ephemeral=True)
                    return
                
                await ctx.response.send_message(embed=Embed(
                    description = f"Deleted profile for <@{ctx.user.id}>",
                    color = Colors.OK
                ), ephemeral=True)
                
            case AccountManagerActions.Create:                
                r = user.create(minecraft=minecraft_username)
                if not r.ok:
                    await ctx.response.send_message(embed=Embed(description=r.error, color=Colors.ERROR), ephemeral=True)
                    return
                
                user.user["whitelist"]["status"] = WLStatus.APPROVED.value
                user.user["whitelist"]["moderator"] = ctx.user.id
                user.user["whitelist"]["reason"] = None
                user.user["whitelist"]["reapply_in"] = None
                user.update()
                
                # Puffer.execute_command(f"/whitelist add {minecraft_username}")
                CWCore.whitelist_add(user.get()['minecraft'])
                
                await ctx.response.send_message(embed=Embed(
                    description = f"Created profile for <@{user.get()['discord']}>\nAttached Minecraft Account: `{user.get()['minecraft']}`",
                    color = Colors.OK
                ), ephemeral=True)