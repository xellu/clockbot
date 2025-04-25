from .config import ConfigManager
from .logging import LoggingManager
from .templates.ConfigTemplate import ConfigTemplate
from .events import builtins, EventBus
from .injector import inject_all
from .database import DatabaseService

import time
import threading

Config = ConfigManager("config.json", template=ConfigTemplate)
WLConfig = ConfigManager("whitelist.json")

Release = "1.0.0"

logger = LoggingManager("Core.Main")
logger.info(f"Running {Config.get('SERVER.NAME')}~{Release}")

DB = DatabaseService(Config)
DB.start()

logger.info("Waiting for services to come online...")
logger.warn("CAUTION: Do not stop, restart or kill the server while services are starting up")
def wait_for_services():
    notifiers = [30, 60, 120, 300, 600]
    max_notifiers = len(notifiers)
    start_time = time.time()

    while True:
        time.sleep(1)

        if not notifiers:
            logger.fatal("Services took too long to come online, possible deadlock, shutting down...")
            EventBus.signal("shutdown.crash", "Services took too long to come online, possible deadlock")

        if time.time() - start_time > notifiers[0]:
            notifiers.pop(0)
            if len(notifiers) < 3:
                logger.fault(f"Services are taking too long to come online, scheduled shutdown in {(notifiers[-1] - time.time() + start_time)/60:.1f} minutes")
                continue

            logger.warn(f"Services are taking too long to come online, please check the logs for errors ({max_notifiers - len(notifiers)}/{max_notifiers})")
            
        if not DB.loaded:
            continue

        logger.success("All services are online, server is ready")
        EventBus.signal("ready")
        break

wait_for_services()

inject_all()

if Config.get("DEVMODE"):
    logger.debug("Running in development mode")