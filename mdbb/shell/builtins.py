from .. import Shell
from . import CommandResponse
from core.events import EventBus
from core import Release, Config
from core.shared import Banner

import os
import threading

@Shell.command("help", "Show this help message", "help [command]", [{"name": "command", "description": "The command to show help for", "required": False}])
def help_command(ctx, command):
    if command is None:
        messages = ["Available commands:", ""]

        for command in Shell.commands:
            messages.append(f"{command['id']}: {command['description']}")

        return CommandResponse(messages)
    else:
        command = Shell.get_command(command)
        if command is None:
            return f"Command {command} not found"
        else:
            return CommandResponse([
                f"Showing help for {command['id']}:",
                command['description'], "",
                
                f"Usage: {command['usage']}", 
                "[] - Optional  /  <> - Required",
                
                "", "Arguments:",
                *[f"{arg['name']} - {arg['description']} {'(required)' if arg['required'] else '(optional)'}" for arg in command['arguments']]
            ])
    
@Shell.command("about", "Show information about MDBB", "about")
def about_command(ctx):
    print(Banner)
    ctx.logger.info(f"Running {Config.get('SERVER.NAME')}, version {Release}")
    
    ctx.logger.info("Infomation")
    ctx.logger.success("Success")
    ctx.logger.warning("Warning")
    ctx.logger.error("Error")
    ctx.logger.debug("Debug")

@Shell.command("stop", "Stop the mdbb service", "stop [--force]")
def stop_command(ctx, *args, **kwargs):
    if kwargs.get("force", False):
        ctx.logger.warning("Issuing force shutdown")
        EventBus.signal("shutdown.force", "Requested by operator")
        return

    ctx.logger.warning("Shutdown procedure initiated, use --force if needed")
    EventBus.signal("shutdown", "Requested by operator")

@Shell.command("clear", "Clear the console", "clear")
def clear_command(ctx):
    os.system("cls" if os.name == "nt" else "clear")
    return "Console was cleared, log file was not affected"

@Shell.command("sync", "Sync the slash commands", "sync")
def sync_command(ctx):
    EventBus.signal("mdbb.sync")
    ctx.logger.info("Command synchronization requested")

@Shell.command("threads", "List all active threads", "threads")
def threads_command(ctx):
    threads = threading.enumerate()
    
    out = ["Active threads:", ""]

    for thread in threads:
        func = thread._target.__name__ if thread._target is not None else thread.ident
        func_loc = thread._target.__module__ if thread._target is not None else "N/A"

        out.append(f"{thread.name} - {func} ({func_loc})")
    return CommandResponse(out)