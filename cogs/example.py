from discord.ext import commands
from discord import app_commands

from mdbb import Bot

class Example(commands.Cog):
    def __init__(self):
        self.bot = Bot

    #example command
    @commands.command()
    async def example(self, ctx, message: str = "Hello, World!"):
        await ctx.reply(message)

    #example slash command
    @app_commands.command(name="example", description="An example slash command")
    @app_commands.describe(message="The message to send")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def example_slash(self, ctx, message: str = "Hello, World!"):
        await ctx.response.send_message(message, ephemeral=True)