import discord
from discord.ext import commands
from discord import app_commands, Embed
from enum import Enum

from mdbb import Bot, Config, CommandLogger, Colors, DB

from core.config import ConfigManager
from core.templates.UserTemplate import UserTemplate, WLStatus
from core.utils import get_mc_username, get_mc_uuid
from core.users import UserManager

from plugins.puffer import Puffer

class AccountManagerActions(Enum):
    Link = "Link"
    Unlink = "Unlink"
    Relink = "Relink"
    
    Create = "Create"
    Delete = "Delete"
    
class ClockAPI(commands.Cog):
    def __init__(self):
        self.bot = Bot

    @app_commands.command(name="migrate", description="Link your Minecraft account to your Discord")
    @app_commands.describe(code="The code you received")
    async def migrate_to_clockapi(self, ctx, code: str):
        user = DB.get("clockbot").users.find_one({"discord": ctx.user.id})
        if user and user["minecraft"]:
            await ctx.response.send_message(embed=Embed(description="You are already linked to a Minecraft account.", color=Colors.ERROR), ephemeral=True)
            return
        
        code = DB.get("clockbot").codes.find_one({"code": code})
        if code is None:
            await ctx.response.send_message(embed=Embed(description="Invalid code.", color=Colors.ERROR), ephemeral=True)
            return
        
        user = UserTemplate()
        user["discord"] = ctx.user.id
        user["minecraft"] = code["uuid"]
        user["whitelist"]["status"] = WLStatus.APPROVED.value
        
        DB.get("clockbot").users.insert_one(user)
        DB.get("clockbot").codes.delete_one({"code": code["code"]})
        
        await ctx.response.send_message(embed=Embed(
            title = "ClockAPI Migration",
            description = f"Thank you for migrating your account to ClockAPI!",
            color = Colors.OK
        ), ephemeral=True)
        
    @app_commands.command(name="profile", description="View your ClockAPI profile")
    async def profile(self, ctx):
        user = UserManager(discord=ctx.user.id).get()
        if not user:
            await ctx.response.send_message(embed=Embed(description="You do not have a ClockAPI profile.", color=Colors.ERROR), ephemeral=True)
            return
        
        await ctx.response.defer(ephemeral=True)
        
        mc_username = get_mc_username(user["minecraft"])
        
        embed = Embed(
            title = "Your Profile",
            description = f"""
**Minecraft:** {mc_username or ''} `{user['minecraft'] or 'NOT LINKED'}`
**Discord:** <@{user['discord']}> `{user['discord']}`

**Last Seen:** {'<t:x:R> <t:x:f>'.replace('x', str(int(user['last_seen']))) if user['last_seen'] else 'Never'}
**Whitelist:** {user['whitelist']["status"]}
            """,
            color = Colors.DEFAULT
        )
        
        embed.set_thumbnail(url=f"https://mc-heads.net/body/{user['minecraft']}")
        
        await ctx.followup.send(embed=embed)
        
    @app_commands.command(name="account", description="Manage user accounts. Users who are created will have automatically approved whitelists.")
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
                
                Puffer.execute_command(f"/whitelist add {minecraft_username}")
                
                await ctx.response.send_message(embed=Embed(
                    description = f"Created profile for <@{user.get()['discord']}>\nAttached Minecraft Account: `{user.get()['minecraft']}`",
                    color = Colors.OK
                ), ephemeral=True)