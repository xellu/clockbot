import discord
from discord.ext import commands, tasks
from discord import app_commands, Embed
from enum import Enum
import time

from mdbb import Config, Bot, Colors, CommandLogger, DB

from core import WLConfig
from core.templates.UserTemplate import UserTemplate, ApplicationTemplate, WLStatus
from core.templates.Messages import apply_for_whitelist_msg
from core.utils import get_mc_username, get_mc_uuid
from core.users import UserManager


class Whitelist(commands.Cog):
    def __init__(self):
        self.bot = Bot
        
        self.guild = self.bot.get_guild(Config.get("WHITELIST.MONITOR.GUILD"))
        self.log_channel = self.bot.get_channel(Config.get("WHITELIST.ANNOUNCE.CHANNEL"))
        self.membership_role = self.bot.get_role(Config.get("WHITELIST.MEMBERSHIP.ROLE"))

   
        self.enabled = Config.get("MODULES.WHITELIST")
        if not self.enabled: return
        
        if not self.guild:
            CommandLogger.error("Whitelist: Guild not found, please check your config")
            self.enabled = False
            
        if not self.log_channel:
            CommandLogger.error("Whitelist: Log channel not found, please check your config")
            self.enabled = False
            
        if not self.membership_role:
            CommandLogger.error("Whitelist: Membership role not found, please check your config")
            self.enabled = False
            
        if not self.enabled:
            CommandLogger.error("Whitelist: Module disabled due to misconfigurations")
            return
        
    
    @tasks.loop(seconds=50)
    