ConfigTemplate = {
    "SERVER.NAME": "mdbb", #name of the app
    "DEVMODE": True, #whether to run in dev mode or not
    
    "BOT.TOKEN": None, #bot token for the bot to login with
    "BOT.PREFIX": "!", #command prefix for the bot
    "BOT.AUTOSYNC": True, #sync the commands with the server on startup
    "BOT.DEFAULTHELP": True, #whether to load the default help command
    "BOT.INSTALLS.SERVER": True, #whether to allow the bot to be installed on the server
    "BOT.INSTALLS.USER": False, #whether to allow users to install it as "user install"
    
    #MongoDB settings
    "MONGO.URL": "mongodb://localhost:27017", #mongodb connection uri
    
    #ClockworkCore credentials
    "CWCORE.IP": "", #ip or domain of the server to be monitored
    "CWCORE.PORT": 0, #port of the server to be monitored
    "CWCORE.KEY": "", #api access key
    "CWCORE.SECRET": "", #encryption secret

    #Modules - Set to True to enable, False to disable
    "MODULES.STATUS": True,
    "MODULES.CHATLINK": True,
    "MODULES.WHITELIST": True,
    
    #Status module settings
    "STATUS.TARGET.IP": "troll.ink", #ip or domain of the server to be monitored
    "STATUS.STATE.CHANNEL": 0, #channel id for a display channel for the server status
    "STATUS.ANNOUNCE.CHANNEL": 0, #channel id for maintenance announcements
    
    #ChatLink module settings
    "CHATLINK.CHANNEL": 0, #channel id for an in-game chat link channel
    
    #Whitelist module settings
    "WHITELIST.MONITOR.GUILD": 0, #guild id for a server to monitor (will de-list people if they leave)
    "WHITELIST.MEMBERSHIP.ROLE": 0, #id of a role to be given to members who are whitelisted
    "WHITELIST.ANNOUNCE.CHANNEL": 0 #id of a channel where whitelist/de-list messages will be sent
}