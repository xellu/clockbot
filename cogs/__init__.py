from mdbb import Bot, EventLogger, EventBus, Config

import sys
from discord.ext import commands, tasks
from discord import app_commands

#add cogs here ⬇️
try:
    from . import (example)
    COGS = [example.Example] 
except Exception as error:
    EventBus.signal("error", error, "Cogs", "Error while importing cogs", fatal=True)

#event handlers------

#bot setup
@Bot.event
async def on_ready():
    #cogs injection
    for cog in COGS:
        try:
            await Bot.add_cog(cog())
        except Exception as error:
            EventBus.signal("error", error, "Cogs", f"Error while injecting cog {cog.__name__}", fatal=True)

    if Config.get("BOT.AUTOSYNC"):
        try:
            EventLogger.info("Synchronizing slash commands")
            await Bot.tree.sync()
        except Exception as error:
            EventBus.signal("error", error, "Cogs", "Error while synchronizing slash commands")

    task_queue_loop.start()

    EventBus.signal("ready")
    EventLogger.success(f"Logged in as {Bot.user}")

@Bot.event
async def on_connect():
    EventLogger.success("Connected to Discord Gateway")

#error handling
@Bot.event
async def on_disconnect():
    EventLogger.error("Disconnected from Discord Gateway")

@Bot.event
async def on_error(event, *args, **kwargs):
    exception = sys.exc_info()[0]
    EventBus.signal("error", exception, "Cogs", f"Error in event {event} (args: {args}, kwargs: {kwargs})")

@Bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

    EventBus.signal("error", error, "Cogs", f"Error in command {ctx.command.name} (ctx: {ctx})")

#tasks------

task_queue = [
    # {
    #     "func": callable,
    #     "async": True,
    #     "args": [],
    #     "kwargs": {}
    # }
]

@tasks.loop(seconds=5)
async def task_queue_loop():
    for task in task_queue:
        if task["async"]:
            await task["func"](*task["args"], **task["kwargs"])
        else:
            task["func"](*task["args"], **task["kwargs"])

    task_queue.clear()

#builtin tasks------

@EventBus.on("mdbb.sync")
def sync_slash_commands_listener():
    task_queue.append({
        "func": sync_slash_commands,
        "async": True,
        "args": [],
        "kwargs": {}
    })

async def sync_slash_commands():
    EventLogger.info("Synchronizing slash commands")
    await Bot.tree.sync()
    EventLogger.success("Slash commands synchronized")