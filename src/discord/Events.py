from src.lib.Discord import Bot, InitCogs
from src.lib.Colors import *

from nautica import Logger, Config
from discord.ext import commands
from discord.interactions import Interaction
from discord import Embed, Member, Guild

from src.lib.Views import WelcomeView

@Bot.event
async def on_ready():
    Logger.ok(f"Logged in as '{Bot.user.name}#{Bot.user.discriminator}'")
    await InitCogs()
    await Bot.tree.sync(guild=Config("clockbot")["servers.discord"])
    
@Bot.event
async def on_member_join(member: Member):
    if member.guild.id != Config("clockbot")["servers.discord"]:
        return
    
    try:
        await member.send(
            embed = Embed(
                title = Config("clockbot")["welcome.title"],
                description = Config("clockbot")["welcome.message"],
                color = INFO
            ),
            view = WelcomeView()
        )
            
    except Exception as e:
        Logger.trace(e)
        await Bot.get_channel(Config("clockbot")["welcome.channelId"]).send(
            f"{member.mention}",
            embed = Embed(
                title = Config("clockbot")["welcome.title"],
                description = Config("clockbot")["welcome.message"],
                color = INFO
            ),
            view = WelcomeView()
        )