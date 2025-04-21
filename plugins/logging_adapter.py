import logging
from logging import Logger as DefaultLogger
from core.logging import LoggingManager

def patch(log: DefaultLogger):
    logger = log.obj

    new_logger = LoggingManager(logger.name)
    if log.silence:
        logger.disabled = True
        return
    
    patcher = Patcher(new_logger)

    logger.info = patcher.info
    logger.log = patcher.info
    logger.warning = patcher.warning
    logger.error = patcher.error
    logger.critical = patcher.error 
    logger.fatal = patcher.error
    logger.exception = patcher.error
    logger.log = patcher.info
    if not log.disable_debug:
        logger.debug = patcher.debug

class Patcher:
    def __init__(self, log: LoggingManager):
        self.log = log

    def info(self, message, *args, **kwargs):
        self.log.info(message % args)

    def debug(self, message, *args, **kwargs):
        self.log.debug(message % args)

    def warning(self, message, *args, **kwargs):
        self.log.warning(message % args)

    def error(self, message, *args, **kwargs):
        self.log.error(message % args)

class LogData:
    def __init__(self, obj: DefaultLogger, silence=False, disable_debug=False):
        self.obj = obj
        self.silence = silence
        self.disable_debug = disable_debug

#----------------

LOGS = [
    LogData(logging.getLogger("discord.client"), disable_debug=True),
    LogData(logging.getLogger("discord.gateway"), disable_debug=True),
    #add more here
]

for log in LOGS:
    patch(log)