from discord import Embed

from mdbb import Colors
from core.users import UserManager

def apply_for_whitelist_msg():
    embed = Embed(
        title = "Apply for Whitelist",
        description = "Click on the button below to get started with your whitelist application.",
        color = Colors.DEFAULT
    )
    embed.set_thumbnail(url="https://minecraft.wiki/images/Book_and_Quill_JE2_BE2.png")
    
    return embed