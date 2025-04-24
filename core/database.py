from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from core.logging import LoggingManager
from .events import EventBus

import threading

logger = LoggingManager("Core.Database")

class DatabaseService:
    """
    A class representing a database service.

    Attributes:
        config (ConfigManager): The configuration object for the database service.
        databases (str[]): A dictionary containing the loaded collections.
    """

    def __init__(self, config):
        self.config = config
        self.client = None
        self.thread = threading.Thread(target=self.connect)
        self.loaded = False

    def start(self):
        self.thread.start()
        logger.info("Connecting to database server")

    def connect(self) -> None:
            """
            Establishes a connection to the MongoDB database.

            Raises:
                Exception: If unable to establish connection to MongoDB.

            Returns:
                None
            """
            try:
                uri = self.config.get("MONGO.URL")
                self.client = MongoClient(uri, server_api=ServerApi('1'))

                try:
                    self.client.admin.command('ping')
                    logger.success("Database connection established")

                    self.loaded = True
                    EventBus.signal("database.ready", self)

                except Exception as e:
                    EventBus.signal("error", e, "Service.Database", str(e), fatal=True)
                    return

            except Exception as e:
                EventBus.signal("error", e, "Service.Database", "Unable to establish connection to MongoDB", fatal=True)
                return

    def get(self, name: str):
        """
        Retrieves a database from the service.
        
        Args:
            name (str): The name of the database to retrieve.
        
        Returns:
            Database object if found, None otherwise.
        """

        return getattr(self.client, name, None)

        return None
    db = get