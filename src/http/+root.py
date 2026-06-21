from napi.http import HTTP, Reply
from nautica.ext.Path import getRoot

@HTTP.GET("/")
async def index():
    return Reply.redirect("/static/index.html"), 301

@HTTP.GET("/whitelist")
async def whitelist():
    return Reply.redirect("/static/whitelist.html"), 301