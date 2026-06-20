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
                
                .add("staff.admins", [], comment="User IDs of admins")
                .add("staff.mods", [], comment="User IDs of moderators")
                
                .add("welcome.channelId", 0, comment="The joins channel, will be used to greet members and display whitelist status")
                .add("welcome.title", "Welcome to my server!", comment="Sent to DMs)")
                .add("welcome.message", "(here's how to get started)", comment="Sent to DMs")
                .add("welcome.donateUrl", "", comment="Leave empty to disable")
                
                .add("chatlink.channelId", 0, comment="Channel to show in-game messages in")
                
                .build()
        )
        
        
Service.Export(ClockConfig, depends_on=["Discord:after"])