ConfigTemplate = {
    "SERVER.NAME": "mdbb", #name of the app
    "DEVMODE": True, #whether to run in dev mode or not
    
    "BOT.TOKEN": None, #bot token for the bot to login with
    "BOT.PREFIX": "!", #command prefix for the bot
    "BOT.AUTOSYNC": True, #sync the commands with the server on startup
    "BOT.DEFAULTHELP": True, #whether to load the default help command
    "BOT.INSTALLS.SERVER": True, #whether to allow the bot to be installed on the server
    "BOT.INSTALLS.USER": False, #whether to allow users to install it as "user install"
    
    #PufferPanel credentials
    "PUFFER.URL": "", #root url
    "PUFFER.SERVER.ID": "", #server id for the minecraft server (this is the server id in the puffer panel)
    "PUFFER.USER": "", #email for the account used for login
    "PUFFER.PASS": "", #account password
    
    
    #Modules - Set to True to enable, False to disable
    "MODULE.STATUS": True,
    "MODULE.CHATLINK": True,
    
    #Status module settings
    "STATUS.TARGET.IP": "troll.ink", #ip or domain of the server to be monitored
    "STATUS.STATE.CHANNEL": 0, #channel id for a display channel for the server status
    "STATUS.ANNOUNCE.CHANNEL": 0, #channel id for maintenance announcements
    
    #ChatLink module settings
    "CHATLINK.CHANNEL": 0, #channel id for an in-game chat link channel
}