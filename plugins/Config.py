from nautica import Service, Config, ConfigBuilder

class ClockConfig(Service):
    def onInstall(self):
        Config.New("clockbot",
            ConfigBuilder()
                .add("servers.discord", 0, comment="ID of the server, that is the 'home' for the bot")
                .add("servers.minecraftIp", "127.0.0.1", comment="IP of the server, that has CWCore installed")
                .add("servers.minecraftPort", 1337, comment="Port for CWCore")
                .add("servers.self", "http://example.com", comment="The domain (with http(s):// & and without '/' at the end) pointing to clockbot itself")
        
                .add("clockwork.secret", "", comment="Encryption key")
                .add("clockwork.key", "", comment="Auth key")
                
                .add("staff.admins", [], comment="Discord role IDs of admins")
                .add("staff.mods", [], comment="Discord role IDs of moderators")
                
                .add("welcome.channelId", 0, comment="The joins channel, will be used to greet members and display whitelist status")
                .add("welcome.title", "Welcome to my server!", comment="Sent to DMs)")
                .add("welcome.message", "(here's how to get started)", comment="Sent to DMs")
                .add("welcome.donateUrl", "", comment="Leave empty to disable")
                
                .add("announcements.channelId", 0, comment="ID of the announcements channel")
                
                .add("chatlink.channelId", 0, comment="Channel to show in-game messages in")
                .add("status.stateChannelId", 0, comment="Voice channel to display state in (i.e. Online, Offline, Maintenance...)")
                .add("status.tpsChannelId", 0, comment="Voice channel to show tps in")
         
                .add("web.name", "My Server", comment="Title to display on your website")
                .add("web.color", "#fad64a", comment="Primary color on the website")
                .add("web.mcIp", "example.com", comment="The minecraft server's IP")
                .add("web.discordInvite", "https://discord.gg/example", comment="Invite to your discord server")
                
                .add("discordOAuth.clientId", 0, comment="https://discord.com/developers/applications")
                .add("discordOAuth.clientSecret", "", comment="Get under Overview > OAuth2; make sure to add (YOUR DOMAIN)/static/auth.html to Redirects")
                # .add("discordOAuth.url", "https://discord.com/oauth2/authorize?client_id=<YOUR CLIENT ID HERE>&response_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A8100%2Fstatic%2Fwhitelist.html&scope=identify", comment="Make sure the redirect url points to (your domain)/static/whitelist.html, and has scope 'identify'")
                
                .build()
        )
        
Service.Export(ClockConfig, depends_on=["Discord:after"])