import os
from .logging import LoggingManager

logger = LoggingManager("Core.Injector")

class injectors:
    def __init__(self):
        pass

    def auto_plugins(self):
        loaded = 0

        if not os.path.exists("plugins"):
            os.makedirs("plugins", exist_ok=True)
            logger.info("Created plugins directory")

        for plugin in os.listdir("plugins"):
            if plugin.endswith(".py"):
                __import__(f"plugins.{plugin[:-3]}")

                loaded += 1

        logger.info(f"Injected {loaded} plugins")

injector = injectors()

def inject_all():
    modules = []

    logger.info("Running task inject_all()")
    for attribute in dir(injector):
        if attribute.startswith("auto_"):
            modules.append( getattr(injector, attribute) )

    logger.info(f"Found {len(modules)} modules to inject")
    for module in modules:
        module()

def inject_module(module: str):
    """
    Runs a specific injection task.

    Arguments:
        module (str): The name of the module to inject.

    Returns:
        Boolean: True if the module was injected successfully, False if not.

    Example:
        inject_module("plugins")
    """
    logger.info("Running task inject_module()")
    for attribute in dir(injector):
        if str(attribute) == module or str(attribute) == f"auto_{module}":
            getattr(injector, attribute)()
            return True
    
    return False