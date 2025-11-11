from services.modelService import ModelService
from validations.chatData import ChatData, ChatMessage
from services.chatBotService import ChatBotService
from fastapi import HTTPException
from services.reviewsService import reviewService
from typing import List, Tuple, Union, Dict,Any
import re


class ModelController:
    def __init__(self):
        # Asumiendo que ModelService maneja la base de datos (guardar historial)
        self.collectionChat = ModelService() 
        self.model_service = ChatBotService()

    async def create_new_chat(self, chat_data: ChatData) -> Tuple[str, Union[str, None]]:
        """
        Coordina la recepción del mensaje, la interacción con el LLM y el guardado.
        Devuelve la respuesta y el nombre del archivo PDF.
        """
        try:
            session_id = chat_data.id_session
            
            # 1. Guardar mensaje del usuario
            self.collectionChat.save_chat(chat_data)
            history_messages: List[ChatMessage] = self.collectionChat.get_messages_by_session_id(session_id)
            # 2 Detectar si el mensaje es un análisis de impacto
            user_message = chat_data.messages[0].message.lower().strip()
            patrones = [
                r"impacto del\s+([\w\s]+)\s+de\s+([\w\s]+)$",
                r"opiniones sobre\s+([\w\s]+)\s+de\s+([\w\s]+)$",
                r"reporte (?:del|de)\s+([\w\s]+)\s+de\s+([\w\s]+)$",
            ]

            producto = None
            empresa = None
            for patron in patrones:
                match = re.search(patron, user_message)
                if match:
                    producto = match.group(1).strip()
                    empresa = match.group(2).strip()
                    break

            #  Si detecta análisis → usar reviewService y devolver resultados
            if producto and empresa:
                resultado = await reviewService.analizar_impacto(empresa, producto)
                if not resultado.get("reseñas_mostradas"):
                    return f"No se encontraron reseñas para {producto} de {empresa}", None

                resumen = resultado["resumen"]
                texto = (
                    f"📊 **Análisis de impacto de {producto} ({empresa})**\n\n"
                    f"- Opiniones positivas: {resumen['positive']}%\n"
                    f"- Opiniones neutras: {resumen['neutral']}%\n"
                    f"- Opiniones negativas: {resumen['negative']}%\n"
                    f"- Total de reseñas: {resumen['total_reviews']}\n\n"
                    f"**Conclusión:** {resultado['conclusion']}"
                )
                return texto, None

            #  Si no es análisis → usar flujo normal del modelo IA
            if self.model_service.model is None:
                await self.model_service.load_model()
            # 3. Llamar al servicio y desempaquetar la tupla
            response_content, pdf_filename = await self.model_service.generate_response_with_history(history_messages)
            
            # 4. Guardar la respuesta de la IA
            ai_message = ChatMessage(types="ai", message=response_content)
            ai_chat_data = ChatData(
                id_session=session_id,
                user_id=chat_data.user_id,
                messages=[ai_message]
            )
            self.collectionChat.save_chat(ai_chat_data)

            # 5. DEVOLVER LA TUPLA para que el router la procese
            return response_content, pdf_filename
            
        except Exception as e:
            # Elevar HTTPException para que FastAPI lo maneje y devuelva un 500
            print(f"Error en create_new_chat: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error interno en el procesamiento del chat: {str(e)}"
            )
        
    async def getSeccionBySession(self, session_id: str) -> List[ChatMessage]:
     """
     Obtiene el historial completo de mensajes para una sesión dada, 
     usando el session_id como parámetro.
     """
     try:
         # 🚨 Se elimina self.collectionChat.save_chat(chat_data)
     
         # 1. Recuperar el historial COMPLETO de la sesión
         history_messages: List[ChatMessage] = self.collectionChat.get_messages_by_session_id(session_id)
     
         # 2. Devolver la lista de mensajes
         return history_messages
     
     except Exception as e:
         print(f"[red]Error en getSeccionBySession: {e}[/red]")
         raise HTTPException(
             status_code=500, 
             detail=f"Error al obtener el historial de la sesión: {str(e)}"
         )
    async def getChatsById(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Busca y retorna todas las sesiones de chat asociadas a un user_id.
        Asume que el Service ya serializa los ObjectId a string.
        """
        try:
            # Llamada al Service. El Service devuelve la lista de diccionarios serializados.
            myHistory: List[Dict[str, Any]] = await self.collectionChat.getChatById(user_id)
            
            return myHistory
            
        except Exception as e:
            # Manejo de error para el router
            print(f"Error en getChatsById: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error al obtener las sesiones de chat por user_id: {str(e)}"
            )