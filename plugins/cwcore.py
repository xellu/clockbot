from core import Config
from core.logging import LoggingManager
from core.events import EventManager, EventBus

import json
import time
import socket
import threading
import base64
import gzip
import os

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad

logger = LoggingManager("Plugins.CWCore")

class CWPackets:
    LOGIN = 0
    CHAT = 1
    STATUS = 2
    HEARTBEAT = 3
    PLAYER_JOIN = 4
    PLAYER_LEAVE = 5
    WL_ADD = 6
    WL_REMOVE = 7

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

class ClockworkCoreAdapter:
    def __init__(self):
        """
        Adapter for Clockwork Core fabric mod.
        """
        self.aes_cipher = AES.new(Config.get("CWCORE.SECRET").encode(), AES.MODE_ECB) 
        self.event = EventManager()
        
        self.socket = None
        
        self.packet_handlers = {
            0: self.handle_login, #login
            1: self.handle_chat, #chat
            2: self.handle_status, #status
            4: self.handle_join, #player join
            5: self.handle_leave, #player leave
        }
        
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
                
    def connect(self):
        """
        Connect to the Clockwork Core API.
        """
        threading.Thread(target=self._connect, daemon=True, name="Adapter.CWCore.Loop").start()
        
    def _connect(self):
        logger.info("Connecting to CWCore API...")
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((Config.get("CWCORE.IP"), Config.get("CWCORE.PORT")))
        except Exception as e:
            EventBus.emit("error", e, "Plugins.CWCore", "Failed to connect to CWCore API",)
            self.drop(f"Failed to connect to CWCore API: {e}", True)
        
        # self.socket.settimeout(30)
        logger.ok("Connected to CWCore API")
        self.event.emit("conn.open")
        
        threading.Thread(target=self.heartbeat, name="Adapter.CWCore.Heartbeat", daemon=True).start()
        self.read_loop()
        
    def drop(self, reason=None, reconnect=True):
        """
        Disconnect from the Clockwork Core API.
        """
        
        logger.warn(f"Dropped connection to CWCore: {reason}")
        self.event.emit("conn.drop", reason)

        self.logged_in = False
        if self.socket:
            try:
                self.socket.close()
            except: pass
            self.socket = None
            
        if reconnect:
            delay = self._reconnect["delays"][self._reconnect["index"]]
            
            logger.info(f"Auto-Reconnecting in {delay}s...")
            time.sleep(delay)
            if self._reconnect["index"] < len(self._reconnect["delays"]) - 1:
                self._reconnect["index"] += 1
            
            logger.info("Reconnecting to CWCore...")
            self._connect()
            
    def heartbeat(self):
        while True:
            if not self.socket:
                break
            
            if not self.logged_in:
                continue
            
            if self.queue: #gradually empty the queue
                self.send(**self.queue.pop(0))
                if not self.queue: logger.ok("Emptied packet queue")
                
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
                
                logger.warn(f"Unknown packet ID: {data['packetId']}")
                    
            except Exception as e:
                EventBus.emit("error", e, "Plugins.CWCore", "Error while reading from CWCore API")
                break
        
        self.drop(f"Socket closed: {self.socket}", True)
        
    def send(self, **kwargs) -> None:
        """
        Send a packet to the Clockwork Core API.
        """
        
        kwargs["time"] = int(time.time())
        kwargs["key"] = Config.get("CWCORE.KEY")
        
        if not self.socket or (not self.logged_in and kwargs["packetId"] != CWPackets.LOGIN):
            self.queue.append(kwargs)
            logger.warn(f"Packet queued: {kwargs}")
            return
        
        _bytes = json.dumps(kwargs).encode("utf-8")
        _encrypted = base64.b64encode(self.aes_cipher.encrypt(pad(_bytes, 16)))
        _compressed = base64.b64encode(gzip.compress(_encrypted))
        
        _prefix = b"clockwork$"
        _full = _prefix + _compressed + b"\n"
        
        
        self.socket.send(_full)
        logger.debug(f"OUT -> {str(kwargs).replace(Config.get('CWCORE.KEY'), 'REDACTED')}")

    def decrypt(self, data: bytes) -> dict:
        """
        Reverse the encryption of the data received from the Clockwork Core API.
        """
        if not data.startswith(b"clockwork$"):
            return {}
        
        # logger.info(f"IN (raw) <- {data.decode('utf-8').replace('\n', '\\n')}")
        
        data = data[len(b"clockwork$"):]
        if os.name != "nt":
            data = data.rstrip(b"\n")
        
        data = gzip.decompress(base64.b64decode(data))
        data = self.aes_cipher.decrypt(base64.b64decode(data))
        data = unpad(data, 16).decode("utf-8")
        data = json.loads(data)
        
        logger.debug(f"IN <- {data}")
        
        return data

    def whitelist_add(self, uuid: str) -> None:
        """
        Add a player to the whitelist.
        """
        self.send(
            packetId = CWPackets.WL_ADD,
            data = {
                "uuid": uuid
            }
        )
        
    def whitelist_remove(self, uuid: str) -> None:
        """
        Remove a player from the whitelist.
        """
        self.send(
            packetId = CWPackets.WL_REMOVE,
            data = {
                "uuid": uuid
            }
        )
        
    def chat_passthrough(self, CWChatMessage) -> None:
        """
        Send a chat message to the Clockwork Core API.
        """
        self.send(
            packetId = CWPackets.CHAT,
            data = {
                "id": CWChatMessage.message_id,
                "author": CWChatMessage.author,
                "content": CWChatMessage.content,
                
                "reply": CWChatMessage.reply,
                "replyData": CWChatMessage.replyData,
                
                "attachments": CWChatMessage.attachments
            }
        )
        
    def handle_login(self, packet, data):
        if data.get("login") == "ok":
            self.logged_in = True
            return
        
        logger.warn(f"Failed to login to CWCore API: {data.get('login')}")
        self.drop(f"Failed to login to CWCore API: {data.get('login')}")
     
    def handle_chat(self, packet, data):
        self.event.emit("chat.message", data)
    
    def handle_status(self, packet, data):
        self.status = {
            "tps": data.get("tps"),
            "online": {
                "count": data.get("playerCount"),
                "max": data.get("maxPlayers"),
                "list": data.get("playerList")
            }
        }
        self.event.emit("status.update")

    def handle_join(self, packet, data):
        self.event.emit("player.join", data)
        
    def handle_leave(self, packet, data):
        self.event.emit("player.leave", data)
    
        
CWCore = ClockworkCoreAdapter()
CWCore.connect()