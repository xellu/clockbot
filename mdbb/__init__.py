from core.bot import Bot, Tree
from core.bot import Tree as Slash
from core import Config
from core.events import EventBus
from core.logging import LoggingManager
from .shell import ShellManager

import threading
from discord import app_commands

CommandLogger = LoggingManager("MDBB.Commands")
EventLogger = LoggingManager("MDBB.Events")
Shell = ShellManager()

if not Config.get("BOT.DEFAULTHELP"):
    Bot.remove_command("help")

Bot.tree.allowed_installs = app_commands.AppInstallationType(guild=Config.get("BOT.INSTALLS.SERVER"), user=Config.get("BOT.INSTALLS.USER"))

threading.Thread(target=Shell.run_loop).start()