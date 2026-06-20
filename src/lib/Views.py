import discord
from discord import ui

from nautica import Config

class WelcomeView(ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(ui.Button(
            label = "Apply for Whitelist",
            url = Config("clockbot")["servers.self"] + "/whitelist",
            style = discord.ButtonStyle.link
        ))
        
        if Config("clockbot")["welcome.donateUrl"]:
            self.add_item(ui.Button(
                label = "Donate",
                url = Config("clockbot")["welcome.donateUrl"],
                style = discord.ButtonStyle.premium
            ))