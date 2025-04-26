import discord
from discord.ext import commands, tasks
from discord import app_commands, Embed
from enum import Enum
import time

from mdbb import Config, Bot, Colors, CommandLogger, DB

from core import WLConfig
from core.templates.UserTemplate import UserTemplate, ApplicationTemplate, WLStatus
from core.templates.Messages import apply_for_whitelist_msg
from core.utils import get_mc_username, get_mc_uuid
from core.users import UserManager

class WhitelistConfigActions(Enum):
    View = "View"
    Set = "Set"
    Get = "Get"
    Setup = "Setup"

class Whitelist(commands.Cog):
    def __init__(self):
        self.bot = Bot
        
        self.apply_category = None
        try:
            self.apply_category = self.bot.get_channel(WLConfig.get("settings", {}).get("category_id", None))
        except:
            CommandLogger.error("Whitelist: Failed to get apply category")
            
        self.delete_old_applications.start()
            

    @app_commands.command(name="configwl", description="Configure the whitelist settings")
    @app_commands.describe(
        action = "Action to perform",
        key = "Key to get/set (if applicable, string)",
        value_str = "Value to set (if applicable, string)",
        value_bool = "Value to set (if applicable, true/false)",
        value_int = "Value to set (if applicable, integer)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def whitelist_config(self, ctx, action: WhitelistConfigActions, key: str = None, value_str: str = None, value_bool: bool = None, value_int: int = None):
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
                        if value_int is None and (not value_str or not value_str.isdigit()):
                            await ctx.response.send_message(embed=Embed(
                                title = "Whitelist Config",
                                description = "Integer value not specified",
                                color = Colors.ERROR
                            ), ephemeral=True)
                            return
                        
                        WLConfig.data["settings"][key] = value_int if value_int is not None else int(value_str)
                        WLConfig.save()
                        
                    await ctx.response.send_message(embed=Embed(
                        title = "Whitelist Config",
                        description = f"Set `{key}` to `{WLConfig.get('settings', {}).get(key)}`",
                        color = Colors.OK
                    ), ephemeral=True)
                    break
                
            case WhitelistConfigActions.Setup:
                await ctx.response.defer(ephemeral=True, thinking=True)
                #send a message to a channel with a button for users to click to get create a whitelist request
                if not value_str or not value_str.isdigit():
                    await ctx.followup.send(embed=Embed(
                        title = "Whitelist Config",
                        description = "Please specify a channel ID as `value_str`",
                        color = Colors.ERROR
                    ), ephemeral=True)
                    return
                
                channel = self.bot.get_channel(int(value_str))
                if not channel:
                    await ctx.followup.send(embed=Embed(
                        title = "Whitelist Config",
                        description = "Channel not found",
                        color = Colors.ERROR
                    ), ephemeral=True)
                    return
                
                msg = await channel.send(
                    embed=apply_for_whitelist_msg(),
                    view = discord.ui.View(timeout=None).add_item(
                        discord.ui.Button(
                            label = "Apply",
                            style = discord.ButtonStyle.primary,
                            custom_id = "wl_apply",
                        )
                    )
                )

                await ctx.followup.send(embed=Embed(
                    title = "Whitelist Config",
                    description = f"Setup completed. Message: {msg.jump_url}",
                    color = Colors.OK
                ), ephemeral=True)
                
    # Create a button handler for the whitelist request button
    # @commands.Cog.listener()
    # async def on_interaction(self, interaction: discord.Interaction):
    #     if interaction.type != discord.InteractionType.component:
    #         return
        
    #     if interaction.data["custom_id"] == "wl_apply":
    #         user = UserManager(discord=interaction.user.id).get()
    #         if not user:
    #             await self.create_apply(interaction)
    #             return
            
    #         #pending status----------------
    #         if user["whitelist"]["status"] in [WLStatus.PENDING.value, WLStatus.INACTIVE.value]:
    #             await interaction.response.send_message(embed=Embed(
    #                 title = "Whitelist",
    #                 description = "You already have a pending whitelist request",
    #                 color = Colors.ERROR
    #             ), ephemeral=True)
    #             return
            
    #         #already whitelisted
    #         if user["whitelist"]["status"] == WLStatus.APPROVED.value:
    #             await interaction.response.send_message(embed=Embed(
    #                 title = "Whitelist",
    #                 description = "You are already whitelisted",
    #                 color = Colors.ERROR
    #             ), ephemeral=True)
    #             return
            
    #         #rejected status---------------- 
    #         if user["whitelist"]["reapply_in"] and user["whitelist"]["reapply_in"] > time.time():
    #             await interaction.response.send_message(embed=Embed(
    #                 title = "Whitelist",
    #                 description = f"You cannot reapply for whitelist until <t:{int(user['whitelist']['reapply_in'])}:F>",
    #                 color = Colors.ERROR
    #             ), ephemeral=True)
    #             return
            
    #         await self.create_apply(interaction)
            
    # async def create_apply(self, interaction: discord.Interaction):
    #     user = UserManager(discord=interaction.user.id)
    #     if not user.is_valid():
    #         user.create_unlinked()
            
    #         user.user["whitelist"]["status"] = WLStatus.PENDING.value
    #         user.update()
            
    #     #create a channel for the user to apply in
    #     if not self.apply_category:
    #         await interaction.response.send_message(embed=Embed(
    #             title = "Whitelist",
    #             description = "Internal error: Could not find apply category",
    #             color = Colors.ERROR
    #         ), ephemeral=True)
    #         return
        
    #     channel = await self.apply_category.create_text_channel(
    #         name=f"wl-application-{interaction.user.name}",
    #         topic=f"Whitelist application for {interaction.user.name}"
    #     )
    #     await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        
    #     if DB.get("clockbot").whitelist.find_one({"user": user.user["discord"]}):
    #         await channel.send(embed=Embed(
    #             title = "Whitelist",
    #             description = "You already have a whitelist application created",
    #             color = Colors.ERROR
    #         ))
    #         return
        
    #     apply = ApplicationTemplate()
    #     apply["user"] = user.user["discord"]
    #     apply["channel"] = channel.id

    #     DB.get("clockbot").whitelist.insert_one(apply)
        
    #     await interaction.response.send_message(embed=Embed(
    #         description = f"Whitelist application created! Please continue in {channel.mention}",
    #         color = Colors.OK
    #     ), ephemeral=True)
    
    # @tasks.loop(seconds=60)
    # async def delete_old_applications(self):
    #     for app in DB.get("clockbot").whitelist.find():
    #         if app["created_at"] + 60 * 60 * 24 * 7 < time.time():
    #             channel = self.bot.get_channel(app["channel"])
    #             if channel:
    #                 await channel.delete()
                
    #             DB.get("clockbot").whitelist.delete_one({"_id": app["_id"]})
    #             CommandLogger.warn(f"Deleted old whitelist application for {app['user']}")
                