import websocket
import requests
import json
import asyncio
import threading
import time
import re

from mdbb import Config
from core.logging import LoggingManager
from core.events import EventManager

logger = LoggingManager("Plugins.Puffer")

class PufferPanelAdapter:
    def __init__(self):
        self.token = self.login()
        
        self.last_heartbeat = None
        self.ws = None
        
        self.connected = False
        
        self.chat_messages = []
        
    def login(self):
        """
        Login to the PufferPanel API and retrieve the token.
        """
        r = requests.post(f"{Config.get('PUFFER.URL')}/auth/login", json={
            "email": Config.get("PUFFER.USER"),
            "password": Config.get("PUFFER.PASS")
        })
        
        if r.status_code != 200:
            logger.error(f"Failed to login to PufferPanel: {r.status_code} - {r.text}")
            return    
        
        logger.ok(f"Logged into PufferPanel as {Config.get('PUFFER.USER')}")
        return r.json().get("session")
    
    def connect(self):
        """
        Connect to the PufferPanel WebSocket API.
        """        
        logger.info("Attempting to connect to PufferPanel WebSocket API...")
        
        loop = asyncio.get_event_loop()
        
        threading.Thread(target=loop.run_until_complete, args=(self.event_loop(),)).start()
        threading.Thread(target=self.heartbeat).start()
    
    async def event_loop(self):
        """
        Connect to the PufferPanel WebSocket API.
        """
        if self.ws:
            return
        
        url = f"{Config.get('PUFFER.URL').replace('http', 'ws')}/proxy/daemon/socket/{Config.get('PUFFER.SERVER.ID')}"
        logger.info(f"Resolving WebSocket URL: {url}")
        self.ws = websocket.WebSocketApp(url,
            header={"cookie": f"puffer_auth={self.token}"},
        
            on_open=self.on_open,    
            on_message=self.on_message,
            on_error=self.on_error,            
        )
        
        
        self.ws.run_forever()
        
        logger.error("WebSocket connection closed. Attempting to reconnect...")
        
        self.connected = False
        self.ws = None
        
        await asyncio.sleep(5)
        await self.reconnect()
    
    def heartbeat(self):
        """
        Send a heartbeat to the PufferPanel WebSocket API.
        """
        while True:
            if self.connected:
                # logger.debug("Sending heartbeat...")
                self.ws.send(json.dumps({"type": "stat"}))
            
            time.sleep(3)
    
    async def reconnect(self):
        """
        Reconnect to the PufferPanel WebSocket API.
        """
        logger.info("Attempting to reconnect to PufferPanel WebSocket API...")
        
        if self.ws:
            self.ws.close()
            self.ws = None
        
        await self.event_loop()
        
    def execute_command(self, command):
        """
        Execute a command on the PufferPanel server.
        """
        if not self.connected:
            logger.error("Not connected to PufferPanel WebSocket API.")
            return
                
        self.ws.send(json.dumps({
            "type": "console",
            "command": command
        }))
        
    def on_message(self, ws, message):
        """
        Handle incoming messages from the PufferPanel WebSocket API.
        """
        #logger.debug(f"Received message: {message}")
        data = json.loads(message)
        # logger.debug(data)
        match data.get("type"):
            case "stat":
                self.last_heartbeat = time.time()
                # logger.debug(f"Heartbeat received: {self.last_heartbeat}")
            
            case "console":
                # logger.debug(f"Console message: {data.get('data')}")
                #[hh:mm:ss] [Server thread/INFO]: <username> message (may have unicode)\r\n
                for ln in data.get("data", {}).get("logs", []):
                    regex = re.compile(r"\[(\d{2}:\d{2}:\d{2})\] \[Server thread/INFO\]: <(.+?)> (.+)")
                    match = regex.match(ln)
                    if match:
                        timestamp, username, message = match.groups()
                        
                        username = self.fix_username(username)
                        
                        self.chat_messages.append({
                            "timestamp": timestamp,
                            "username": username,
                            "message": message
                        })
                    
            
            case _:
                logger.warning(f"Unknown message type: {data.get('type')}")
    
    def on_open(self, ws):
        """
        Handle the opening of the WebSocket connection.
        """
        logger.info("WebSocket connection opened.")
        
        self.connected = True
        logger.ok("Connected to PufferPanel WebSocket API.")
    
    def on_error(self, ws, error):
        """
        Handle errors from the PufferPanel WebSocket API.
        """
        logger.error(f"WebSocket error: {error}")
    
    
    def fix_username(self, name):
        """
        Fix the username to be more readable.
        """
        roles = {
            "§c★§r": "`⭐ Admin`",
            "§aD§r": "`💖 Donator`",
            "[AFK]": "`💤 AFK`",
        }
        
        for role, replacement in roles.items():
            name = name.replace(role, replacement)
    
        return name
    
Puffer = PufferPanelAdapter()
Puffer.connect()