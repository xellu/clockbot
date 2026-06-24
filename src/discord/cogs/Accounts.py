import discord
from discord import Embed, app_commands
from discord.ext import commands, tasks
from enum import Enum

from src.lib.Discord import AddCog
from src.lib.Colors import *
from src.lib.User import UserManager
from src.lib.Util import escape_md, get_mc_username, get_mc_uuid
from src.lib.Clockwork import CW

from nautica import Services, Config, Logger
from plugins.CWEvents import PlayerJoinEvent

class Accounts(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @app_commands.command(name="profile", description="View your ClockAPI profile")
    async def profile(self, ctx: discord.Interaction):
        await ctx.response.defer(thinking=True)
        user = UserManager(discord=ctx.user.id)
        if not user.is_valid():
            await ctx.response.send_message(embed=Embed(description="You do not have a ClockAPI profile.", color=ERROR), ephemeral=True)
            
        seen = user.get_seen(md=True)
        await ctx.followup.send(
            embed = Embed(
                title = "Your Profile",
                description = f"""
**Minecraft:** {escape_md(get_mc_username(user.get('minecraft'))) or ''} `{user.get('minecraft') or 'NOT LINKED'}`
**Discord:** {ctx.user.mention} `{ctx.user.id}`

**Last Seen:** {seen.meta if seen.ok else seen.error}
**Whitelist:** {user.get()['whitelist']["status"]}
                """,
                color = INFO
            )
            .set_thumbnail(url=f"https://mc-heads.net/body/{user.get()['minecraft']}")
        )
    
    @app_commands.command(name="account-create", description="Create profile for users")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(
        user = "User to manage",
        minecraft_username = "Minecraft account to attach"
    )
    async def acc_create(self, ctx: discord.Interaction, user: discord.User, minecraft_username: str):
        await ctx.response.defer(ephemeral=False)

        u = UserManager(discord=user.id)
        r = u.create(minecraft=minecraft_username)
        if not r.ok:
            return await ctx.followup.send(embed=Embed(description=r.error, color=ERROR))
        
        u.whitelist_approve(ctx.user.id)
        
        await ctx.followup.send(embed=Embed(
            description = f"Created profile for {user.mention}\n> Attached Account: {get_mc_username(u.get('minecraft'))} `{u.get('minecraft')}`",
            color = OK
        ))
        
    @app_commands.command(name="account-delete", description="Delete a user's profile")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(
        user = "User to manage",
    )
    async def acc_Delete(self, ctx: discord.Interaction, user: discord.User):
        await ctx.response.defer(ephemeral=False)
        u = UserManager(discord=user.id)
        r = u.delete()
        if not r.ok:
            return await ctx.followup.send(embed=Embed(description=r.error, color=ERROR))
            
        await ctx.followup.send(embed=Embed(
            description = f"Deleted profile for {user.mention}",
            color = OK
        ))
        
    @app_commands.command(name="account-link", description="Link a minecraft account to an existing ClockBot account")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(
        user = "User to manage",
        minecraft_username = "Minecraft account to attach"
    )
    async def acc_link(self, ctx: discord.Interaction, user: discord.User, minecraft_username: str):
        await ctx.response.defer(ephemeral=False)

        u = UserManager(discord=user.id)
        r = u.link(minecraft_username)
        if not r.ok:
            await ctx.followup.send(embed=Embed(description=r.error, color=ERROR))
            return
        
        await ctx.followup.send(embed=Embed(
            description = f"Linked a Minecraft account {escape_md(minecraft_username)} `{user.get()['minecraft']}` to {user.mention}'s profile",
            color = OK
        ))  

    @app_commands.command(name="account-relink", description="Remove and attach a minecraft account to an existing ClockBot account")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(
        user = "User to manage",
        minecraft_username = "Minecraft account to attach"
    )
    async def acc_relink(self, ctx: discord.Interaction, user: discord.User, minecraft_username: str):
        await ctx.response.defer(ephemeral=False)

        u = UserManager(discord=user.id)
        r = u.relink(minecraft_username)
        if not r.ok:
            await ctx.followup.send(embed=Embed(description=r.error, color=ERROR))
            return
        
        await ctx.followup.send(embed=Embed(
            description = f"Re-linked the Minecraft account {escape_md(minecraft_username)} to {user.mention}'s profile",
            color = OK
        ))
        
    
    @app_commands.command(name="account-unlink", description="Detach a minecraft account from a ClockBot account")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(
        user = "User to manage",
    )
    async def acc_Delete(self, ctx: discord.Interaction, user: discord.User):
        await ctx.response.defer(ephemeral=False)
        u = UserManager(discord=user.id)
        uuid = u.get('minecraft')

        r = u.unlink()
        if not r.ok:
            return await ctx.followup.send(embed=Embed(description=r.error, color=ERROR))
            
        await ctx.followup.send(embed=Embed(
            description = f"Unlinked Minecraft account (`{uuid}`) from {user.mention}'s profile",
            color = OK
        ))
    
AddCog(Accounts)