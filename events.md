# Built-In Events

error <error: Exception> [source: str] [message: str] [fatal: bool] - Is emitted when an error is detected.
warn <message: str> - A Warning message event
config.load <data: ConfigTemplate> - Called once ConfigManager loads the file contents
shutdown [reason: str] - Call to shutdown the bot
shutdown.force [reason: str] - Call to force shutdown the bot
shutdown.crash [reason: str] - Will cause the bot to crash shutdown
start - Called when the bot is starting up
ready - Called when the bot is fully loaded and ready to accept commands

# Built-In Handlers
- We've included some built-in event handlers for you to use. You can find them in `core/events/builtins.py`

These include handlers for the following events:
1. `error` - Logs the error to the console using LoggingManager. Could crash shutdown the bot, if the `fatal` flag is set to True.
2. `warn` - Logs the warning message to the console using LoggingManager.
3. `shutdown` - Properly shuts down the bot.
4. `shutdown.force` - Forcefully shuts down the bot. Should be used with caution.
5. `shutdown.crash` - Forcefully shuts down the bot, used by the error handler to crash shutdown the bot.
6. `start` - Will cause the bot to start connecting to Discord.