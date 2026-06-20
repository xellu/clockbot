# from core import Config
# from core.logging import LoggingManager
# from core.events import EventManager, EventBus
# from core.utils import get_mc_username, get_mc_uuid

from nautica import Logger, Config, Service, Scheduler

import json
import time
import socket
import threading
import base64
import gzip
import asyncio
from plugins.CWEvents import *

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad

class CWPackets:
    LOGIN = 0
    CHAT = 1
    STATUS = 2
    HEARTBEAT = 3
    PLAYER_JOIN = 4
    PLAYER_LEAVE = 5
    WL_ADD = 6
    WL_REMOVE = 7
    WL_LIST = 8
    BROADCAST = 9
    KICK = 69

class CWChatMessage:
    def __init__(self, message_id: int, author: str, content: str, attachments: list[str] | None = None):
        self.message_id = message_id
        self.author = author
        self.content = content
        self.reply = False
        self.replyData = {}
        self.attachments = attachments if attachments else []
        
    def add_reply(self, message_id: int, author: str, content: str) -> None:
        """
        Add a reply to the chat message.
        """
        self.reply = True
        self.replyData = {
            "id": message_id,
            "author": author,
            "content": content
        }
        
    def toJson(self):
        return {
            "messageId": self.message_id,
            "member": self.author,
            "content": self.content,
            "reply": self.replyData,
            "attachments": self.attachments
        }
        
class Clockwork(Service):
    def __init__(self):
        """
        Adapter for Clockwork Core fabric mod.
        """
        super().__init__()
        
        self.aes_cipher = None
        
        self.socket = None
        
        self.packet_handlers = {
            0: self.handle_login, #login
            1: self.handle_chat, #chat
            2: self.handle_status, #status
            4: self.handle_join, #player join
            5: self.handle_leave, #player leave
            8: self.handle_wl_list, #whitelist list
        }
        
        self.on_chat = []
        self.on_join = []
        self.on_leave = []
        self.on_status = []
        self.on_wl_list = []
        
        self.logged_in = False
        self.last_heartbeat = 0
        
        self._reconnect = {
            "delays": [0, 5, 5, 10, 10, 30, 60, 120, 300],
            "index": 0
        }
        
        self.status = {
            "tps": 0,
            "online": {
                "count": 0,
                "max": 0,
                "list": []
            }
        }
        
        self.queue = []
        
        self.chat_messages = []
        self.player_joins = []
        self.player_leaves = []
        self.system_messages = []
                
    def onSetup(self, registry):
        self.aes_cipher = AES.new(Config("clockbot")["clockwork.secret"].encode(), AES.MODE_ECB) 
    
    def onStart(self, registry):
        self.connect()
        
    def onClose(self, reason):
        self.drop(reason, reconnect=False)

    def connect(self):
        """
        Connect to the Clockwork Core API.
        """
        threading.Thread(target=self._connect, daemon=True, name="Adapter.CWCore.Loop").start()
        
    def _connect(self):
        Logger.info("Connecting to Clockwork API...")
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((Config("clockbot")["servers.minecraftIp"], Config("clockbot")["servers.minecraftPort"]))

        except Exception as e:
            # EventBus.emit("error", e, "Plugins.CWCore", "Failed to connect to CWCore API",)
            Logger.trace(e)
            self.drop(f"Failed to connect to Clockwork API: {e}", silent=True)
        
        # self.socket.settimeout(30)
        Logger.ok("Connected to Clockwork API")
        
        threading.Thread(target=self.heartbeat, name="Adapter.CWCore.Heartbeat", daemon=True).start()
        self.read_loop()
        
    def drop(self, reason=None, reconnect=True, silent=False):
        """
        Disconnect from the Clockwork Core API.
        """
        
        Logger.warn(f"Clockwork connection dropped: {reason}")

        self.logged_in = False
        if self.socket:
            try:
                self.socket.close()
            except: pass
            self.socket = None
            
        if reconnect:
            delay = self._reconnect["delays"][self._reconnect["index"]]
            
            Logger.info(f"Auto-Reconnecting in {delay}s...")
            time.sleep(delay)
            if self._reconnect["index"] < len(self._reconnect["delays"]) - 1:
                self._reconnect["index"] += 1
            
            Logger.info("Reconnecting to Clockwork API...")
            self._connect()
            
    def heartbeat(self):
        while True:
            if not self.socket:
                break
            
            if not self.logged_in:
                continue
            
            if self.queue: #gradually empty the queue
                self.send(**self.queue.pop(0))
                if not self.queue: Logger.ok("Emptied packet queue")
                
            if time.time() - self.last_heartbeat > 5:
                self.send(
                    packetId = CWPackets.HEARTBEAT,
                    data = {}
                )
                self.last_heartbeat = time.time()
            
            time.sleep(1/3)
            
    def read_loop(self):        
        self.send(
            packetId = CWPackets.LOGIN,
            data = {}
        )
        while self.socket:
            try:
                data = self.socket.recv(1024*64)
                if not data:
                    break
                
                data = self.decrypt(data)
                if not data:
                    continue
                
                handler = self.packet_handlers.get(data["packetId"])
                if handler:
                    handler(data, data["data"])
                    continue
                
                Logger.warn(f"Unknown packet ID: {data['packetId']}")
                    
            except ConnectionAbortedError:
                Logger.warn("Connection aborted")
                return
            
            except Exception as e:
                Logger.trace(e)
                break
        
        self.drop(f"Socket closed: {self.socket}", True)
        
    def send(self, **kwargs) -> None:
        """
        Send a packet to the Clockwork Core API.
        """
        
        kwargs["time"] = int(time.time())
        kwargs["key"] = Config("clockbot")["clockwork.key"]
        
        if not self.socket or (not self.logged_in and kwargs["packetId"] != CWPackets.LOGIN):
            self.queue.append(kwargs)
            kwargs.pop("key")
            Logger.warn(f"Packet queued: {kwargs}")
            return
        
        _bytes = json.dumps(kwargs).encode("utf-8")
        _encrypted = base64.b64encode(self.aes_cipher.encrypt(pad(_bytes, 16)))
        _compressed = base64.b64encode(gzip.compress(_encrypted))
        
        _prefix = b"clockwork$"
        _full = _prefix + _compressed + b"\n"
        
        
        self.socket.send(_full)
        Logger.debug(f"OUT -> {str(kwargs).replace(Config("clockbot")["clockwork.key"], 'REDACTED')}")

    def decrypt(self, data: bytes) -> dict:
        """
        Reverse the encryption of the data received from the Clockwork Core API.
        """
        if not data.startswith(b"clockwork$"):
            return {}
        
        # logger.info(f"IN (raw) <- {data.decode('utf-8').replace('\n', '\\n')}")
        
        
        data = data.replace(b"clockwork$", b"")
        # logger.debug(data)

        data = self.decode_b64(data)
        # logger.debug(data)
        
        data = gzip.decompress(data)
        data = base64.b64decode(data)
        
        data = self.aes_cipher.decrypt(data)
        data = unpad(data, 16).decode("utf-8")
        data = json.loads(data)
        
        Logger.debug(f"IN <- {data}")
        
        return data

    def decode_b64(self, data: bytes) -> bytes:
        string_base64 = data.decode()
        string_base64 = string_base64.strip('=')
        data_len = len(string_base64) % 4
        if data_len == 1:
            string_base64 = string_base64[:-1]
        elif data_len:
            padding_len = 4 - data_len
            string_base64 += padding_len * '='
        decodedBytes = base64.b64decode(string_base64)
        return decodedBytes
        
    def WhitelistAdd(self, uuid: str) -> None:
        """
        Add a player to the whitelist.
        """
        self.send(
            packetId = CWPackets.WL_ADD,
            data = {
                "uuid": uuid
            }
        )
        
    def WhitelistRemove(self, uuid: str) -> None:
        """
        Remove a player from the whitelist.
        """
        self.send(
            packetId = CWPackets.WL_REMOVE,
            data = {
                "uuid": uuid
            }
        )
        
    def SendChatMessage(self, msg: CWChatMessage) -> None:
        """
        Send a chat message to the Clockwork Core API.
        """
        self.send(
            packetId = CWPackets.CHAT,
            data = {
                "id": msg.message_id,
                "author": msg.author,
                "content": msg.content,
                
                "reply": msg.reply,
                "replyData": msg.replyData,
                
                "attachments": msg.attachments
            }
        )
        
    def GetWhitelist(self) -> None:
        """
        Request the whitelist from the Clockwork Core API.
        """
        self.send(
            packetId = CWPackets.WL_LIST,
            data = {}
        )
        
        
    def KickPlayer(self, uuid: str, reason: str) -> None:
        """
        Kick a player from the server.
        """
        self.send(
            packetId = CWPackets.KICK,
            data = {
                "uuid": uuid,
                "reason": reason
            }
        )
        # logger.error(f"Kick player is not implemented in CWCore API")
        
    def BroadcastMessage(self, message: list[dict]) -> None:
        """
        Broadcast a /tellraw message to all players on the server.
        """
        self.send(
            packetId = CWPackets.BROADCAST,
            data = {
                "content": json.dumps(message),
            }
        )
        
    def handle_login(self, packet, data):
        if data.get("login") == "ok":
            self._reconnect["index"] = 0
            self.logged_in = True
            return
        
        Logger.warn(f"Failed to login to Clockwork API: {data.get('login')}")
        self.drop(f"Failed to login to Clockwork API: {data.get('login')}")
     
    #gotta update this later---------
    def handle_chat(self, packet, data):
        from src.lib.Discord import Bot

        event = ChatMessageEvent.fromJson(data)
        for subscriber in self.on_chat:
            asyncio.run_coroutine_threadsafe(subscriber(event), Bot.loop)
    
    def handle_status(self, packet, data):
        from src.lib.Discord import Bot

        self.status = {
            "tps": data.get("tps"),
            "online": {
                "count": data.get("playerCount"),
                "max": data.get("maxPlayers"),
                "list": data.get("playerList")
            }
        }
        event = StatusUpdateEvent.fromJson(data)        
        for subscriber in self.on_status:
            asyncio.run_coroutine_threadsafe(subscriber(event), Bot.loop)

    def handle_join(self, packet, data):
        from src.lib.Discord import Bot

        event = PlayerJoinEvent.fromJson(data)
        for subscriber in self.on_join:
            asyncio.run_coroutine_threadsafe(subscriber(event), Bot.loop)
        
    def handle_leave(self, packet, data):
        from src.lib.Discord import Bot

        event = PlayerLeaveEvent.fromJson(data)
        for subscriber in self.on_leave:
            asyncio.run_coroutine_threadsafe(subscriber(event), Bot.loop)
        
    def handle_wl_list(self, packet, data):
        Logger.error("Unhandled packet: handle_wl_list")
        
    def onChatMessage(self):
        def decorator(func):
            self.on_chat.append(func)
            return func
    
        return decorator
            
    def onPlayerJoin(self):
        def decorator(func):
            self.on_join.append(func)
            return func
    
        return decorator
    
    def onPlayerLeave(self):
        def decorator(func):
            self.on_leave.append(func)
            return func
    
        return decorator
    
    def onStatusUpdate(self):
        def decorator(func):
            self.on_status.append(func)
            return func
    
        return decorator
    
    # def onWhitelistGet(self):
    #     def decorator(func):
    #         self.on_wl_list.append(func)
    #         return func
    
    #     return decorator
    
    
Service.Export(Clockwork, depends_on=["ClockConfig", "Discord:after"])