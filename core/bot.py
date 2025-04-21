import discord

from discord.ext import commands
from discord import app_commands

from . import Config
from .events import EventBus

Bot =  commands.Bot(command_prefix=Config.get("BOT.PREFIX"), intents=discord.Intents.all()) 
Tree = Bot.tree

def run():
    try:
        if not Config.get("BOT.TOKEN"):
            raise Exception("Authentication token is missing. Please check your configuration file.") 

        Bot.run(Config.get("BOT.TOKEN"))
    except Exception as e:
        EventBus.signal("error", e, "Core.Bot", "Failed to start bot", fatal=True)