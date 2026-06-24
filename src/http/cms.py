from napi.http import HTTP, Reply
from nautica import Config

@HTTP.GET()
async def branding():
    return Reply(
        name = Config("clockbot")["web.name"],
        color = Config("clockbot")["web.color"],
        
        mcIp = Config("clockbot")["web.mcIp"],
        discordInvite = Config("clockbot")["web.discordInvite"],
        
        discordClientId = str(Config("clockbot")["discordOAuth.clientId"]),
        domain = Config("clockbot")["servers.self"],
    )