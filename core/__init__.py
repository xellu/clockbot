from .config import ConfigManager
from .logging import LoggingManager
from .templates.ConfigTemplate import ConfigTemplate
from .events import builtins, EventBus
from .injector import inject_all

import threading

Config = ConfigManager("config.json", template=ConfigTemplate)

Release = "1.0.0"

logger = LoggingManager("Core.Main")
logger.info(f"Running {Config.get('SERVER.NAME')}~{Release}")

inject_all()

if Config.get("DEVMODE"):
    logger.debug("Running in development mode")