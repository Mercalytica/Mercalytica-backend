from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from config.env import EnvConfig
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig:
     def __init__(self):
          env = EnvConfig()
          mongo_url = env.get("MONGO_URL", "mongodb://localhost:27017")
          db_name = env.get("DB_NAME", "competition_manager")
          
          try:
               self.client = MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
               # Verificar conexión
               self.client.admin.command('ping')
               self.db = self.client[db_name]
               logger.info(f"✅ Conectado a MongoDB: {db_name}")
          except (ServerSelectionTimeoutError, Exception) as e:
               logger.warning(f"⚠️ MongoDB no disponible: {e}")
               logger.warning("Usando modo offline - chat_memory no persistirá")
               self.client = None
               self.db = None

     def get_collection(self, collection_name: str):
          if self.db is None:
               raise RuntimeError(
                    "MongoDB no está disponible. "
                    "Asegúrate de que MongoDB está corriendo en localhost:27017"
               )
          return self.db[collection_name]