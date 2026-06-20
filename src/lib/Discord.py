
from nautica import Services

import discord
from discord.ext import commands

Bot: commands.Bot = commands.Bot(
    help_command=None,
    command_prefix = "!",
    intents = discord.Intents.all()
)

Services.get("Discord").Bot = Bot

_cogs: list[commands.Cog] = []
def AddCog(cog: commands.Cog):
    global _cogs
    _cogs.append(cog(Bot))
    
async def InitCogs():
    for cog in _cogs:
        await Bot.add_cog(cog)
        
def GetCogs():
    return _cogs
