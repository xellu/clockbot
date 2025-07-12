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

def warn_message(target, reason, moderator, expire):
    return [
    "",
    {
        "color": "yellow",
        "text": "\u2588\u2588\u2588\u2588\u2588\u2588\u2588"
    },
    {
        "color": "gray",
        "text": " ==========["
    },
    {
        "bold": True,
        "color": "yellow",
        "text": " Clock"
    },
    {
        "bold": True,
        "color": "aqua",
        "text": "Mod"
    },
    {
        "color": "gray",
        "text": " ]==========="
    },
    {
        "text": "\n"
    },
    {
        "color": "yellow",
        "text": "\u2588\u2588\u2588"
    },
    {
        "color": "black",
        "text": "\u2588"
    },
    {
        "color": "yellow",
        "text": "\u2588\u2588\u2588"
    },
    {
        "color": "yellow",
        "text": f" {target} was warned "
    },
    {
        "text": "\n"
    },
    {
        "color": "yellow",
        "text": "\u2588\u2588\u2588"
    },
    {
        "color": "black",
        "text": "\u2588"
    },
    {
        "color": "yellow",
        "text": "\u2588\u2588\u2588"
    },
    {
        "color": "gray",
        "text": " -"
    },
    {
        "color": "dark_aqua",
        "text": " Reason:"
    },
    {
        "color": "aqua",
        "text": f" \"{reason}\""
    },
    {
        "text": "\n"
    },
    {
        "color": "yellow",
        "text": "\u2588\u2588\u2588"
    },
    {
        "color": "black",
        "text": "\u2588"
    },
    {
        "color": "yellow",
        "text": "\u2588\u2588\u2588"
    },
    {
        "color": "gray",
        "text": " -"
    },
    {
        "color": "dark_aqua",
        "text": " Moderator:"
    },
    {
        "color": "aqua",
        "text": f" {moderator} "
    },
    {
        "text": "\n"
    },
    {
        "color": "yellow",
        "text": "\u2588\u2588\u2588\u2588\u2588\u2588\u2588 "
    },
    {
        "text": "\n"
    },
    {
        "color": "yellow",
        "text": "\u2588\u2588\u2588"
    },
    {
        "color": "black",
        "text": "\u2588"
    },
    {
        "color": "yellow",
        "text": "\u2588\u2588\u2588"
    },
    {
        "color": "gray",
        "italic": True,
        "text": f" This warning expires in {expire}"
    },
    {
        "text": "\n"
    },
    {
        "color": "yellow",
        "text": "\u2588\u2588\u2588\u2588\u2588\u2588\u2588"
    },
    {
        "color": "gray",
        "text": " ================================"
    }
]
    
def kick_message(target, reason, moderator):
    return [
    "",
    {
        "color": "red",
        "text": "\u2588\u2588\u2588\u2588\u2588\u2588\u2588"
    },
    {
        "color": "gray",
        "text": " ==========["
    },
    {
        "bold": True,
        "color": "yellow",
        "text": " Clock"
    },
    {
        "bold": True,
        "color": "aqua",
        "text": "Mod"
    },
    {
        "color": "gray",
        "text": " ]==========="
    },
    {
        "text": "\n"
    },
    {
        "color": "red",
        "text": "\u2588\u2588\u2588"
    },
    {
        "color": "white",
        "text": "\u2588"
    },
    {
        "color": "red",
        "text": "\u2588\u2588\u2588"
    },
    {
        "color": "yellow",
        "text": f" {target} was kicked "
    },
    {
        "text": "\n"
    },
    {
        "color": "red",
        "text": "\u2588\u2588\u2588"
    },
    {
        "color": "white",
        "text": "\u2588"
    },
    {
        "color": "red",
        "text": "\u2588\u2588\u2588"
    },
    {
        "color": "gray",
        "text": " -"
    },
    {
        "color": "dark_aqua",
        "text": " Reason:"
    },
    {
        "color": "aqua",
        "text": f" \"{reason}\""
    },
    {
        "text": "\n"
    },
    {
        "color": "red",
        "text": "\u2588\u2588\u2588"
    },
    {
        "color": "white",
        "text": "\u2588"
    },
    {
        "color": "red",
        "text": "\u2588\u2588\u2588"
    },
    {
        "color": "gray",
        "text": " -"
    },
    {
        "color": "dark_aqua",
        "text": " Moderator:"
    },
    {
        "color": "aqua",
        "text": f" {moderator} "
    },
    {
        "text": "\n"
    },
    {
        "color": "red",
        "text": "\u2588\u2588\u2588\u2588\u2588\u2588\u2588 "
    },
    {
        "text": "\n"
    },
    {
        "color": "red",
        "text": "\u2588\u2588\u2588"
    },
    {
        "text": "\u2588"
    },
    {
        "color": "red",
        "text": "\u2588\u2588\u2588"
    },
    {
        "text": " \n"
    },
    {
        "color": "red",
        "text": "\u2588\u2588\u2588\u2588\u2588\u2588\u2588"
    },
    {
        "color": "gray",
        "text": " ================================"
    }
]
    
def ban_message(target, reason, moderator, expire):
    return [
    "",
    {
        "color": "dark_red",
        "text": "\u2588\u2588\u2588\u2588\u2588\u2588\u2588"
    },
    {
        "color": "gray",
        "text": " ==========["
    },
    {
        "bold": True,
        "color": "yellow",
        "text": " Clock"
    },
    {
        "bold": True,
        "color": "aqua",
        "text": "Mod"
    },
    {
        "color": "gray",
        "text": " ]==========="
    },
    {
        "text": "\n"
    },
    {
        "color": "dark_red",
        "text": "\u2588\u2588\u2588"
    },
    {
        "color": "white",
        "text": "\u2588"
    },
    {
        "color": "dark_red",
        "text": "\u2588\u2588\u2588"
    },
    {
        "color": "yellow",
        "text": f" {target} was banned "
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
        "text": "\u2588\u2588\u2588"
    },
    {
        "color": "gray",
        "text": " -"
    },
    {
        "color": "dark_aqua",
        "text": " Reason:"
    },
    {
        "color": "aqua",
        "text": f" \"{reason}\""
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
        "text": "\u2588\u2588\u2588"
    },
    {
        "color": "gray",
        "text": " -"
    },
    {
        "color": "dark_aqua",
        "text": " Moderator:"
    },
    {
        "color": "aqua",
        "text": f" {moderator} "
    },
    {
        "text": "\n"
    },
    {
        "color": "dark_red",
        "text": "\u2588\u2588\u2588\u2588\u2588\u2588\u2588 "
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
        "text": "\u2588\u2588\u2588"
    },
    {
        "color": "gray",
        "italic": True,
        "text": f" This ban expires in {expire}"
    },
    {
        "text": "\n"
    },
    {
        "color": "dark_red",
        "text": "\u2588\u2588\u2588\u2588\u2588\u2588\u2588"
    },
    {
        "color": "gray",
        "text": " ================================"
    }
]