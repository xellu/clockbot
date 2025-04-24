import discord
from discord.ext import commands
from discord import app_commands, Embed
import enum

from mdbb import Bot, Config, CommandLogger, Colors, DB

from core.config import ConfigManager
from core.templates.UserTemplate import UserTemplate
from core.utils import get_mc_username

from plugins.puffer import Puffer

WLApply = ConfigManager("whitelist.json") #questions for whitelist applications

class WhitelistPlayerAction(enum.Enum):
    ADD = "add"
    REMOVE = "remove"
    

class Whitelist(commands.Cog):
    def __init__(self):
        self.bot = Bot

    @app_commands.command(name="migrate", description="Link your Minecraft account to your Discord")
    @app_commands.describe(code="The code you received")
    async def migrate_to_clockapi(self, ctx, code: str):
        user = DB.get("clockbot").users.find_one({"discord": ctx.user.id})
        if user:
            await ctx.response.send_message(embed=Embed(description="You are already linked to a Minecraft account.", color=Colors.ERROR), ephemeral=True)
            return
        
        code = DB.get("clockbot").codes.find_one({"code": code})
        if code is None:
            await ctx.response.send_message(embed=Embed(description="Invalid code.", color=Colors.ERROR), ephemeral=True)
            return
        
        user = UserTemplate()
        user["discord"] = ctx.user.id
        user["minecraft"] = code["uuid"]
        user["whitelisted"] = True
        
        DB.get("clockbot").users.insert_one(user)
        DB.get("clockbot").codes.delete_one({"code": code["code"]})
        
        await ctx.response.send_message(embed=Embed(
            title = "ClockAPI Migration",
            description = f"Thank you for migrating your account to ClockAPI!",
            color = Colors.OK
        ), ephemeral=True)
        
    @app_commands.command(name="profile", description="View your ClockAPI profile")
    async def profile(self, ctx):
        user = DB.get("clockbot").users.find_one({"discord": ctx.user.id})
        if user is None:
            await ctx.response.send_message(embed=Embed(title="Account not Found", color=Colors.ERROR), ephemeral=True)
            return
        
        await ctx.response.defer(ephemeral=True)
        
        mc_username = get_mc_username(user["minecraft"])
        
        embed = Embed(
            title = "Your Profile",
            description = f"""
**Minecraft:** {mc_username} `{user['minecraft']}`
**Discord:** <@{user['discord']}> `{user['discord']}`

**Last Seen:** {'<t:x:R>'.replace('x', str(int(user['last_seen']*1000))) if user['last_seen'] else 'Never'}
**Whitelisted:** {user['whitelisted']}
            """,
            color = Colors.DEFAULT
        )
        
        embed.set_thumbnail(url=f"https://mc-heads.net/body/{user['minecraft']}")
        
        await ctx.followup.send(embed=embed)