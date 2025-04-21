from . import EventBus
from core.logging import LoggingManager

import traceback
import threading
import os

logger = LoggingManager("Core.Events")

fallback = {
    "source": "MDBB",
    "error": "An error occurred in the MDBB service",
    "warning": "An issue was detected in the MDBB service"
}

#Error handler-------------

@EventBus.on("error")
def error_callback(error: Exception, source: str = fallback["source"], message: str = fallback["error"], fatal: bool = False):
    from core import Config

    logger.error(f"Error in {source}: {error}")

    if Config.get("DEVMODE"):
        traceback.print_exc()

    if fatal:
        EventBus.signal("shutdown.crash", f"Fatal error in {source}: {message}")

@EventBus.on("warn")
def warn_callback(source: str=fallback["source"], message: str=fallback["warning"]):
    logger.warning(f"{source}: {message}")


#Shutdown handlers---------------

@EventBus.on("shutdown")
def shutdown(reason: str = None):
    threading.Thread(target=shutdown_thread, args=(reason,)).start()
    
def shutdown_thread(reason: str = None):
    try:
        logger.info(f"Core shutdown requested ({reason or 'no reason provided'})")

        logger.success("Services offline, shutting down core")
        os._exit(0)
    except Exception as e:
        logger.error(f"Failed to shutdown core, overriding ({e})")
        EventBus.signal("error", e, "Core.Events", "Failed to shutdown core", fatal=True)

@EventBus.on("shutdown.force")
def force_shutdown(reason: str = None):
    logger.warning(f"Force shutdown requested ({reason or 'no reason provided'})")
    os._exit(0)

@EventBus.on("shutdown.crash")
def crash_shutdown(reason: str = None):
    logger.error(f"Core crash protocol initiated")
    logger.error(f"Exit Message: {reason}")
    os._exit(1)

