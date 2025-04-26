from core import Config
from core.logging import LoggingManager
from core.events import EventManager, EventBus

import json
import time
import socket
import threading
import base64
import gzip

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

class ClockworkCoreAdapter:
    def __init__(self):
        """
        Adapter for Clockwork Core fabric mod.
        (An alternative to PufferPanel API)
        """
        self.aes_cipher = AES.new(Config.get("CWCORE.SECRET").encode(), AES.MODE_ECB) 
        self.event = EventManager()
        
        self.socket = None
        
        self.packets = {
            0: None, #login
            1: None, #chat
            2: None, #status
            
        }
        
        self.logged_in = False
        self.last_heartbeat = 0
        
        self._reconnect = {
            "delays": [0, 5, 5, 10, 10, 30, 60, 120, 300],
            "index": 0
        }
        
    def connect(self):
        """
        Connect to the Clockwork Core API.
        """
        threading.Thread(target=self._connect, daemon=True, name="Adapter.CWCore.Loop").start()
        
    def _connect(self):
        logger.info("Connecting to Clockwork Core API...")
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((Config.get("CWCORE.IP"), Config.get("CWCORE.PORT")))
        except Exception as e:
            EventBus.emit("error", e, "Plugins.CWCore", "Failed to connect to Clockwork Core API", True)
        
        # self.socket.settimeout(30)
        logger.ok("Connected to Clockwork Core API")
        
        threading.Thread(target=self.heartbeat, name="Adapter.CWCore.Heartbeat", daemon=True).start()
        self.read_loop()
        
    def drop(self, reason=None, reconnect=False):
        """
        Disconnect from the Clockwork Core API.
        """
        
        logger.warn(f"Dropped connection to Clockwork Core API: {reason}")
        if self.socket:
            try:
                self.socket.close()
            except: pass
            self.socket = None
            
        if reconnect:
            logger.info("Reconnecting to Clockwork Core API...")
            self.connect()
            
    def heartbeat(self):
        while True:
            return
            
    def read_loop(self):        
        self.send(
            packetId = CWPackets.LOGIN,
            data = {}
        )
        while self.socket:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                
                data = self.decrypt(data)
                # if data["packetId"] == 0:
                    # self.send(
                    #     packetId = CWPackets.CHAT,
                    #     data = {
                    #         "id": 0,
                    #         "author": "John Doe",
                    #         "content": "hul pero zmrde!",
                            
                    #         "reply": False,
                    #         # "replyData": {
                    #         #     "id": 0,
                    #         #     "author": "Jane Doe",
                    #         #     "content": "smrdis!",
                    #         # },
                            
                    #         "attachments": ["https://xellu.xyz/attachments/1.png", "https://google.com/chui"],
                    #     }
                    # )
                    # self.send(
                    #     packetId = CWPackets.WL_REMOVE,
                    #     data = {
                    #         "uuid": "860ea469-9468-4296-be1a-fb8121a8e57d"
                    #     }
                    # )
                    
            except Exception as e:
                EventBus.emit("error", e, "Plugins.CWCore", "Error while reading from Clockwork Core API")
                break
        
        self.drop(f"Socket closed: {self.socket}", True)
        
    def send(self, **kwargs) -> None:
        """
        Send a packet to the Clockwork Core API.
        """
        
        kwargs["time"] = int(time.time())
        kwargs["key"] = Config.get("CWCORE.KEY")
        
        if not self.socket:
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
        
        data = data[len(b"clockwork$"):]
        data = gzip.decompress(base64.b64decode(data))
        data = self.aes_cipher.decrypt(base64.b64decode(data))
        data = unpad(data, 16).decode("utf-8")
        data = json.loads(data)
        
        logger.debug(f"IN <- {data}")
        
        return data

CWCore = ClockworkCoreAdapter()

if Config.get("API.SOURCE").lower() == "cwcore":
    logger.info("Selected ChatLink channel: CWCore")
    CWCore.connect()
            
            