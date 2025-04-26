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

def migration_notice(code):
    return [
        "",
        {
            "text": "\n\n\n\n\n"
        },
        {
            "color": "dark_red",
            "text": "\u2588\u2588\u2588\u2588\u2588\u2588\u2588"
        },
        {
            "bold": True,
            "color": "red",
            "text": " >"
        },
        {
            "bold": True,
            "color": "yellow",
            "text": ">"
        },
        {
            "bold": True,
            "color": "red",
            "text": "> ClockBot Migration NOTICE <"
        },
        {
            "bold": True,
            "color": "yellow",
            "text": "<"
        },
        {
            "bold": True,
            "color": "red",
            "text": "<"
        },
        {
            "text": "\n"
        },
        {
            "color": "dark_red",
            "text": "\u2588\u2588\u2588"
        },
        {
            "text": "\u2588"
        },
        {
            "color": "dark_red",
            "text": "\u2588\u2588\u2588 "
        },
        {
            "color": "yellow",
            "text": "Your account hasn't been"
        },
        {
            "text": "\n"
        },
        {
            "color": "dark_red",
            "text": "\u2588\u2588\u2588"
        },
        {
            "text": "\u2588"
        },
        {
            "color": "dark_red",
            "text": "\u2588\u2588\u2588 "
        },
        {
            "color": "yellow",
            "text": "yet migrated to ClockAPI"
        },
        {
            "text": "\n"
        },
        {
            "color": "dark_red",
            "text": "\u2588\u2588\u2588"
        },
        {
            "text": "\u2588"
        },
        {
            "color": "dark_red",
            "text": "\u2588\u2588\u2588 "
        },
        {
            "text": "\n"
        },
        {
            "color": "dark_red",
            "text": "\u2588\u2588\u2588\u2588\u2588\u2588\u2588 "
        },
        {
            "text": "Use "
        },
        {
            "color": "aqua",
            "text": f"/migrate {code} "
        },
        {
            "text": "on Discord\n"
        },
        {
            "color": "dark_red",
            "text": "\u2588\u2588\u2588"
        },
        {
            "text": "\u2588"
        },
        {
            "color": "dark_red",
            "text": "\u2588\u2588\u2588 "
        },
        {
            "text": "to migrate your account.\n"
        },
        {
            "color": "dark_red",
            "text": "\u2588\u2588\u2588\u2588\u2588\u2588\u2588 "
        },
        {
            "color": "gray",
            "text": "- The Clockwork Team"
        },
        {
            "text": "\n "
        }
    ]