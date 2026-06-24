from nautica import Service, Logger
from nautica.services.builtins.shell.decorator import RegisterCommand, CommandRequirements
from napi import Require
from src.lib.User import UserManager


class Commands(Service):
    def onSetup(self, registry):
        @RegisterCommand("admin", "Add or remove site admins", CommandRequirements(args={"action": Require.AnyOf("add", "remove"), "discordId": int}))
        def admin(action: str, discordId: int):
            user = UserManager(discord=discordId)
            if not user.is_valid():
                return "User not found"
            
            match action.lower():
                case "add":
                    user.user["isAdmin"] = True
                    user.update()
                    return "Made user a website admin"
                case "remove":
                    user.user["isAdmin"] = False
                    user.update()
                    return "Removed user from website admins list"

    def isEnabled(self):
        return True
    
Service.Export(Commands, depends_on=["Shell"])