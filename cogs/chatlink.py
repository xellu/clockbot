from discord.ext import commands, tasks
from discord import app_commands, Embed
import json
import time

from mdbb import Bot, Config, CommandLogger, Colors, DB
from core.utils import get_mc_username, get_mc_uuid, random_str
from core.templates.Messages import migration_notice

from plugins.puffer import Puffer

class ChatLink(commands.Cog):
    def __init__(self):
        self.bot = Bot
        self.channel = self.bot.get_channel(Config.get("CHATLINK.CHANNEL"))
        
        if not Config.get("MODULES.CHATLINK"): return
        