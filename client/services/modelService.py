from config.database import DatabaseConfig
from validations.chatData import ChatData,ChatMessage
from typing import List, Optional,Dict,Any
from fastapi import HTTPException
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class ModelService:
     def __init__(self):
          try:
               db_config = DatabaseConfig()
               self.collectionChat = db_config.get_collection("chat_memory")
               self.db_available = True
          except RuntimeError as e:
               logger.warning(f"MongoDB no disponible: {e}")
               self.collectionChat = None
               self.db_available = False
               self._in_memory_chat = {}  # Almacenamiento en memoria como fallback
     
     def save_chat(self, chat_data: ChatData):
          if not self.db_available:
               # Guardar en memoria
               key = f"{chat_data.user_id}:{chat_data.id_session}"
               if key not in self._in_memory_chat:
                    self._in_memory_chat[key] = {"user_id": chat_data.user_id, "id_session": chat_data.id_session, "messages": []}
               
               if isinstance(chat_data.messages, ChatMessage):
                    self._in_memory_chat[key]["messages"].append(chat_data.messages.dict())
               elif isinstance(chat_data.messages, list):
                    self._in_memory_chat[key]["messages"].extend([m.dict() for m in chat_data.messages])
               return
          
          if isinstance(chat_data.messages, ChatMessage):
               message_doc = chat_data.messages.dict()
          elif isinstance(chat_data.messages, list):
               message_doc = {"$each": [m.dict() for m in chat_data.messages]}
          else:
               raise ValueError("chat_data.messages debe ser ChatMessage o List[ChatMessage]")

          self.collectionChat.update_one(
               {"user_id": chat_data.user_id, "id_session": chat_data.id_session},
               {"$push": {"messages": message_doc}},
               upsert=True
          )
     
     def get_messages_by_session_id(self, id_session: str) -> List[ChatMessage]:
          if not self.db_available:
               # Recuperar de memoria
               for key, data in self._in_memory_chat.items():
                    if data.get("id_session") == id_session:
                         return [
                              ChatMessage(types=msg['types'], message=msg['message'])
                              for msg in data.get('messages', [])
                         ]
               return []
          
          chat_document = self.collectionChat.find_one(
               {"id_session": id_session},
               {"messages": 1, "_id": 0} 
          )
          
          if chat_document and 'messages' in chat_document:
               return [
                    ChatMessage(types=msg['types'], message=msg['message'])
                    for msg in chat_document['messages']
               ]
          
          return []
     
     @staticmethod
     def serialize_mongo_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
          """Convierte ObjectId a string en un documento de MongoDB para JSON."""
          if doc is None:
               return None
          
          serialized_doc = doc.copy() 
          
          # Convierte el ObjectId a string
          if "_id" in serialized_doc and isinstance(serialized_doc["_id"], ObjectId):
               serialized_doc["_id"] = str(serialized_doc["_id"])
               
          return serialized_doc
    
     async def getChatById(self, user_id: str) -> List[Dict[str, Any]]:
          """
          Busca y retorna TODAS las sesiones de chat asociadas a un user_id.
          Aplica serialización para convertir ObjectId a string.
          """
          try:
               if not self.db_available:
                    # Recuperar de memoria
                    chats = [data for data in self._in_memory_chat.values() if data.get("user_id") == user_id]
                    return chats
               
               # Obtener del cursor
               chat_cursor = self.collectionChat.find({"user_id": user_id})
               chats = list(chat_cursor) 
               serialized_chats = [ModelService.serialize_mongo_doc(chat) for chat in chats] 
               return serialized_chats
    
          except Exception as e:
               logger.error(f"Error en ModelService.getChatById: {e}")
               return []