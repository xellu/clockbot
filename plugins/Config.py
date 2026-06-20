from nautica import Service, Config, ConfigBuilder

class ClockConfig(Service):
    def onInstall(self):
        Config.New("clockbot",
            ConfigBuilder()
                .add("servers.discord", 0, comment="ID of the server, that is the 'home' for the bot")
                .add("servers.minecraftIp", "127.0.0.1", comment="IP of the server, that has CWCore installed")
                .add("servers.minecraftPort", 1337, comment="Port for CWCore")
                .add("servers.self", "http://example.com", comment="The domain (with http(s):// & and without '/' at the end) pointing to clockbot itself")
        
                
                .add("welcome.channelId", 0, comment="The joins channel, will be used to greet members and display whitelist status")
                .add("welcome.title", "Welcome to my server!", comment="Sent to DMs)")
                .add("welcome.message", "(here's how to get started)", comment="Sent to DMs")
                .add("welcome.donateUrl", "", comment="Leave empty to disable")
                
                
                .build()
        )
        
        
Service.Export(ClockConfig)