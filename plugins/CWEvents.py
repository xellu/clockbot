from src.lib.Util import escape_md

class Player:
    def __init__(self, name, uuid):
        self.name = name
        self.name_escaped = escape_md(name)
        self.uuid = uuid
    
    @staticmethod
    def fromJson(data):
        return Player(
            data["name"],
            data["uuid"]
        )

class Event:
    def fromJson(self, data):
        ...

class ChatMessageEvent(Event):
    def __init__(self, author: Player, content: str):
        self.author = author
        self.content = content
    
    @staticmethod
    def fromJson(data):
        return ChatMessageEvent(
            author = Player.fromJson(data['author']),
            content = data['content']
        )
    
class StatusUpdateEvent(Event):
    def __init__(self, tps: float, playerCount: int, maxPlayers: int, playerList: list[Player]):
        self.tps: float = tps
        self.playerCount: int = playerCount
        self.maxPlayers: int = maxPlayers
        self.playerList: list[Player] = playerList
    
    @staticmethod
    def fromJson(data):
        return StatusUpdateEvent(
            tps = data['tps'],
            playerCount = data['playerCount'],
            maxPlayers = data['maxPlayers'],
            playerList = [Player.fromJson(p) for p in data['playerList']]
        )

class PlayerJoinEvent(Event):
    def __init__(self, player: Player):
        self.player: Player = player
        
    @staticmethod
    def fromJson(data):
        return PlayerJoinEvent(
            Player.fromJson(data)
        )

class PlayerLeaveEvent(Event):
    def __init__(self, player: Player):
        self.player: Player = player
        
    @staticmethod
    def fromJson(data):
        return PlayerLeaveEvent(
            Player.fromJson(data)
        )
        
