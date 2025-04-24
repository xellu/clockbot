from core.bot import Bot, Tree
from core.bot import Tree as Slash
from core import Config, DB
from core.events import EventBus
from core.logging import LoggingManager
from .shell import ShellManager

import threading
from discord import app_commands

CommandLogger = LoggingManager("MDBB.Commands")
EventLogger = LoggingManager("MDBB.Events")
Shell = ShellManager()

class Colors:
    DEFAULT = 0x5997FF
    OK = 0x59FF6E
    ERROR = 0xFF5959
    WARNING = 0xFFC85F

if not Config.get("BOT.DEFAULTHELP"):
    Bot.remove_command("help")

Bot.tree.allowed_installs = app_commands.AppInstallationType(guild=Config.get("BOT.INSTALLS.SERVER"), user=Config.get("BOT.INSTALLS.USER"))

threading.Thread(target=Shell.run_loop).start()