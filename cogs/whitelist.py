import discord
from discord.ext import commands, tasks
from discord import app_commands, Embed
from enum import Enum

from mdbb import Config, Bot, Colors, CommandLogger, DB

from core import WLConfig
from core.templates.UserTemplate import UserTemplate, WLStatus
from core.utils import get_mc_username, get_mc_uuid

class WhitelistConfigActions(Enum):
    View = "View"
    Set = "Set"
    Get = "Get"

class Whitelist(commands.Cog):
    def __init__(self):
        self.bot = Bot

    @app_commands.command(name="configwl", description="Configure the whitelist settings")
    @app_commands.describe(
        action = "Action to perform",
        key = "Key to get/set (if applicable, string)",
        value_str = "Value to set (if applicable, string)",
        value_bool = "Value to set (if applicable, true/false)",
        value_int = "Value to set (if applicable, integer)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def whitelist_config(self, ctx, action: WhitelistConfigActions, key: str = None, value_str: str = None, value_bool: bool = None, value_int: bool = None):
        match action:
            case WhitelistConfigActions.View:
                content = []
                for k, v in WLConfig.get("settings", {}).items():
                    content.append(f"{k}=`{v}`")
                    
                await ctx.response.send_message(embed=Embed(
                    title = "Whitelist Config",
                    description = "\n".join(content),
                    color = Colors.DEFAULT
                ), ephemeral=True)
    
            case WhitelistConfigActions.Get:
                if not key:
                    await ctx.response.send_message(embed=Embed(
                        title = "Whitelist Config",
                        description = "Key not specified",
                        color = Colors.ERROR
                    ), ephemeral=True)
                    return
                
                for k, v in WLConfig.get("settings", {}).items():
                    if k != key:
                        continue
                    
                    await ctx.response.send_message(embed=Embed(
                        title = f"Whitelist Config: {k}",
                        description = f"Value: `{v}` ({type(v).__name__})",
                        color = Colors.DEFAULT
                    ), ephemeral=True)
                    break
                else:
                    await ctx.response.send_message(embed=Embed(
                        title = "Whitelist Config",
                        description = f"Key `{key}` not found",
                        color = Colors.ERROR
                    ), ephemeral=True)
                    
            case WhitelistConfigActions.Set:
                if not key:
                    await ctx.response.send_message(embed=Embed(
                        title = "Whitelist Config",
                        description = "Key not specified",
                        color = Colors.ERROR
                    ), ephemeral=True)
                    return
                
                for k, v in WLConfig.get("settings", {}).items():
                    if k != key:
                        continue
                    
                    if type(v) == str:
                        if not value_str:
                            await ctx.response.send_message(embed=Embed(
                                title = "Whitelist Config",
                                description = "String value not specified",
                                color = Colors.ERROR
                            ), ephemeral=True)
                            return
                        
                        WLConfig.data["settings"][key] = value_str
                        WLConfig.save()
                        
                    elif type(v) == bool:
                        if value_bool is None:
                            await ctx.response.send_message(embed=Embed(
                                title = "Whitelist Config",
                                description = "Boolean value not specified",
                                color = Colors.ERROR
                            ), ephemeral=True)
                            return
                        
                        WLConfig.data["settings"][key] = value_bool
                        WLConfig.save()
                        
                    elif type(v) == int:
                        if value_int is None:
                            await ctx.response.send_message(embed=Embed(
                                title = "Whitelist Config",
                                description = "Integer value not specified",
                                color = Colors.ERROR
                            ), ephemeral=True)
                            return
                        
                        WLConfig.data["settings"][key] = value_int
                        WLConfig.save()
                        
                    await ctx.response.send_message(embed=Embed(
                        title = "Whitelist Config",
                        description = f"Set `{key}` to `{WLConfig.get('settings', {}).get(key)}`",
                        color = Colors.OK
                    ), ephemeral=True)
                    break