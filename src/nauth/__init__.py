
from nautica import Services
from plugins.nauth import NAuth, NAuthSession
from src.lib.User import UserManager

Auth: NAuth = Services.get("NAuth")
# Usage:
# from src.nauth import Auth
# @Auth.Protect() <- on a route you want protected by auth

# Define a profile getter
def profile_getter(session: NAuthSession):
    return UserManager(discord=session.refId)

# Configure the Auth
Auth.Configure() \
    .setProfileGetter(profile_getter) \
    .addCookieKey("session") \
    .addHeaderKey("Authorization")
