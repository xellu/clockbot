from core.logging import LoggingManager
from core.events import EventBus

logger = LoggingManager("MDBB.Shell")

class ShellManager:
    def __init__(self):
        self.commands = [
            # {
            #     "id": "help",
            #     "description": "Show this help message",
            #     "usage": "help",
            #     "arguments": [{
            #         "name": "command",
            #         "description": "The command to show help for",
            #         "required": False
            #     }],
            #     "function": callable
            # }
        ]
        self.logger = logger

    #command decorator
    def command(self, id: str, description: str = "No description", usage: str | None = None, arguments: list | None = None):
        def decorator(function):
            self.commands.append({
                "id": id,
                "description": description,
                "usage": usage if usage else id,
                "arguments": arguments if arguments is not None else [],
                "function": function
            })
        return decorator

    def get_command(self, id: str):
        for command in self.commands:
            if command["id"] == id:
                return command
            
        return None
    
    def run_command(self, command: str):
        #parse command (command [arg1] [arg2] --flag)
        args = command.split(" ")
        command = args[0].lower()
        args = args[1:]

        cmd = self.get_command(command)
        if not cmd:
            logger.error(f"Command {command} not found")
            return None
        
        #parse arguments
        data = {
            "args": [],
            "flags": {}
        }

        for arg in cmd["arguments"]:
            if arg["required"]:
                if len(args) == 0:
                    logger.error(f"Argument {arg['name']} is required")
                    return None

                data["args"].append(args.pop(0))
            else:
                if len(args) > 0:
                    data["args"].append(args.pop(0))
                else:
                    data["args"].append(None)

        #parse flags
        for arg in args:
            if arg.startswith("--"):
                flag = arg[2:]
                data["flags"][flag] = True


        return cmd["function"](self, *data["args"], **data["flags"])

    def run_loop(self):
        from . import builtins

        while True:
            try: #detect ctrl+c
                command = input("")
            except:
                logger.warn("Shutdown requested")
                EventBus.signal("shutdown", "Requested by operator")
                continue

            try: #detect command errors
                r = self.run_command(command)
            except Exception as e:
                EventBus.signal("error", e, "MDBB.Shell", f"Failed to execute a command: {e}")
                continue

            if r is not None:
                if isinstance(r, CommandResponse):
                    for message in r.messages:
                        logger.info(message)
                else:
                    logger.info(r)

class CommandResponse:
    def __init__(self, messages: str | list):
        if isinstance(messages, str):
            messages = [messages]
        
        self.messages = messages