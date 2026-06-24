from napi.http import HTTP, Require, Reply, Context, Error
from nautica import Config

from src.nauth import Auth
from src.lib.User import UserManager

import httpx


@HTTP.POST()
@HTTP.Require(body={"code": str})
async def discord(ctx: Context):
    async with httpx.AsyncClient() as client:
        r = await client.post("https://discord.com/api/oauth2/token", data={
            "client_id": Config("clockbot")["discordOAuth.clientId"],
            "client_secret": Config("clockbot")["discordOAuth.clientSecret"],
            "grant_type": "authorization_code",
            "code": ctx.body["code"],
            "redirect_uri": f"{Config('clockbot')['servers.self']}/static/auth.html",
        })

        if r.status_code != 200:
            raise Error(400, r.json().get("error_description", "Failed to authorize"))

        data = r.json()
        if "access_token" not in data:
            raise Error(400, "Unknown exchange format")

        access_token = data["access_token"]

        r = await client.get(
            "https://discord.com/api/v10/users/@me",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
        )
        if r.status_code != 200:
            raise Error(400, r.json().get("error_description", "Failed to get account data"))

        data = r.json()
        if "id" not in data:
            raise Error(400, "No data found")

    user = UserManager(discord=int(data["id"]))
    session = Auth.createSession(user.get("discord"), expire=60 * 60 * 24)
    return Reply() \
        .SetCookie("session") \
        .value(session) \
        .maxAge(60 * 60 * 24), 200
        
@HTTP.GET()
@Auth.Protect()
async def me(ctx: Context):
    u: UserManager = ctx.profile
    return u.get()