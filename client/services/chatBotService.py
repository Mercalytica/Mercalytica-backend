from config.llm import getModel
from helpers.extractResponse import extraer_respuesta_aimessage
from validations.chatData import ChatMessage 
from typing import List, Tuple, Union
import datetime
import os 
from fpdf import FPDF
from rich import print

PDF_DIR = "reports_generated"
os.makedirs(PDF_DIR, exist_ok=True)


class ChatBotService:
    """
    Servicio de chatbot con protecciones contra inyección de prompts
    y revelación de instrucciones del sistema.
    """
    
    # Palabras clave que indican intento de extraer el system prompt
    PROMPT_INJECTION_KEYWORDS = [
        "system prompt",
        "dame tu promt system"
        "system message",
        "tu prompt",
        "tu instrucción",
        "tu sistema",
        "tus reglas",
        "ignore the above",
        "olvida lo anterior",
        "forget everything",
        "olvida todo",
        "ignora todo",
        "prompts anteriores",
        "instrucciones anteriores",
        "actúa como",
        "comportate como",
        "pretend you are",
        "your instructions are",
        "tus instrucciones son",
        "reveal your prompt",
        "muestra tu prompt",
        "dime tu prompt",
        "cuál es tu prompt",
        "rol anterior",
        "tu verdadero rol",
        "jailbreak",
        "rol secreto",
        "persona verdadera"
    ]
    
    def __init__(self):
        self.model = None
        self.fecha_actual = datetime.datetime.now()

    def _is_prompt_injection_attempt(self, message: str) -> bool:
        """
        Detecta si el mensaje intenta hacer inyección de prompts
        o extraer el system prompt.
        """
        message_lower = message.lower().strip()
        
        # Verificar palabras clave sospechosas
        for keyword in self.PROMPT_INJECTION_KEYWORDS:
            if keyword in message_lower:
                return True
        
        # Patrones adicionales comunes
        suspicious_patterns = [
            r"show.*prompt",
            r"reveal.*instruction",
            r"what.*your.*role",
            r"cuéntame.*instrucciones",
            r"desconecta.*protocolo",
            r"disable.*safety",
            r"remove.*restriction"
        ]
        
        import re
        for pattern in suspicious_patterns:
            if re.search(pattern, message_lower):
                return True
        
        return False

    async def load_model(self):
        self.model = await getModel()
        if self.model is None:
            raise RuntimeError("El modelo no se pudo cargar. getModel() devolvió None.")

    async def generate_response_with_history(self, history_messages: List[ChatMessage]) -> Tuple[str, Union[str, None]]:
        """
        Genera la respuesta del modelo y el PDF si se solicita un reporte.
        Devuelve (response_text, pdf_filename)
        
        Incluye protecciones contra inyección de prompts.
        """
        if self.model is None:
            raise RuntimeError("No se puede generar respuesta: el modelo no está cargado. Llama a load_model() primero.")
        
        # Verificar el último mensaje del usuario para detectar intentos de inyección
        if history_messages and history_messages[-1].types == "user":
            user_message = history_messages[-1].message
            if self._is_prompt_injection_attempt(user_message):
                # Bloquear la solicitud y retornar respuesta segura
                safe_response = (
                    "No puedo proporcionar esa información. "
                    "Estoy aquí para ayudarte con análisis de mercado y búsquedas sobre productos. "
                    "¿Hay algo sobre un producto o mercado en el que pueda ayudarte?"
                )
                return safe_response, None
        
        try:
            SYSTEM_PROMPT = f"""
            Eres un Asistente Analítico de Mercado (AAM). Tu rol es proporcionar análisis concisos, precisos y profesionales sobre productos, empresas y tendencias del mercado.

		  **REGLAS Y FUNCIONALIDAD:**
		  
		  1. Rol: Actúa siempre como un analista profesional de mercado.
		  2. Memoria: Mantén la coherencia con el historial de la sesión.
		  3. Herramientas disponibles: Tienes acceso a herramientas para:
		     - Realizar búsquedas web sobre reseñas de productos
		     - Buscar menciones en redes sociales (Twitter, Instagram, Facebook, Reddit, TikTok, YouTube, LinkedIn)
		     - Analizar sentimientos en reseñas y opiniones
		     - Extraer características clave (positivas y negativas) de las opiniones
		     - Acceder a datos de base de datos sobre usuarios, empresas, productos y órdenes
		  
		  **BÚSQUEDA WEB Y REDES SOCIALES:**
		  
		  4. Cuando el usuario pregunte sobre reseñas, opiniones o impacto en redes sociales de un producto:
		     - Utiliza la herramienta "buscar_resenas_producto" para encontrar opiniones en la web
		     - Utiliza "buscar_menciones_redes_sociales" para buscar en plataformas específicas
		     - Combina los resultados para proporcionar un análisis comprehensivo
		  5. Después de obtener reseñas, utiliza las herramientas de análisis:
		     - "analizar_sentimiento_resenas" para determinar si las opiniones son positivas o negativas
		     - "extraer_caracteristicas_resenas" para identificar qué aspectos son mejor/peor valorados
		  
		  **GENERACIÓN DE REPORTE (PDF):**
		  
		  6. Si el usuario solicita un reporte formal o análisis completo, debes iniciar la respuesta **EXACTAMENTE** con la etiqueta: **[REPORTE_INICIADO]**.
		  7. NO uses la etiqueta `[REPORTE_INICIADO]` para consultas informales.
		  8. La fecha para cualquier reporte es: {datetime.datetime.now().strftime("%d/%m/%Y")}.
		  
		  **FORMATO DEL TEXTO (CRÍTICO - PARA PDF BÁSICO):**
		  
		  9. **INICIO:** Después de la etiqueta `[REPORTE_INICIADO]`, **NO añadas símbolos decorativos (ej: ***,****, ---) ni líneas vacías.** Comienza el texto del reporte inmediatamente en la siguiente línea.
		  10. **NO uses formato Markdown.** Esto incluye: NO usar negritas (`**`), cursivas (`*`), ni listas con guiones o asteriscos (`-`, `*`).
		  11. **Estructura Visual:** Para simular encabezados y secciones, usa **TEXTO EN MAYÚSCULAS** y separa los párrafos y secciones con un doble salto de línea (dos `ENTER`).
		  
		  **OBJETIVO:** El texto entregado debe ser un bloque limpio, plano y estructurado únicamente con mayúsculas y saltos de línea.
            """
            
            formatted_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for msg in history_messages:
                role = "user" if msg.types == "user" else "assistant"
                formatted_messages.append({"role": role, "content": msg.message})
                
            response = await self.model.ainvoke({"messages": formatted_messages})
		  
            print(response)
            
            response_text = extraer_respuesta_aimessage(response["messages"][-1])
            
            print(response_text)

            
            
            pdf_filename = None
            
            if "[REPORTE_INICIADO]" in response_text:
                pdf_content = response_text.replace("[REPORTE_INICIADO]", "").strip()
                
                pdf_filename = self._generate_report_pdf(pdf_content)
                
                response_text = f"**[PDF Creado]**\nSu análisis ha sido completado y generado en formato PDF. Puede descargarlo a través del enlace.\n\n{pdf_content}"
            
            return response_text, pdf_filename

        except Exception as e:
            # En caso de error, devuelve un mensaje de error y no se genera PDF
            print(f"Error en generate_response_with_history: {e}")
            return f"ERROR: Fallo al procesar la solicitud del modelo. Por favor, inténtelo de nuevo. Detalle: {str(e)}", None
  
    def _generate_report_pdf(self, content: str) -> str:
        """Función interna para crear y guardar el archivo PDF."""
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_title('Reporte de Análisis de Mercado (AAM)')
        
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 15, 'Reporte Analítico Generado por AAM', 0, 1, 'C')

        fecha_hora = self.fecha_actual.strftime("%d-%m-%Y %H:%M:%S")
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 5, f'Fecha de Generación: {fecha_hora}', 0, 1, 'R')
        pdf.ln(5)

        pdf.set_font('Arial', '', 12)
        # Usar utf-8 para manejar caracteres especiales
        pdf.multi_cell(0, 7, content) 

        timestamp = self.fecha_actual.strftime("%Y%m%d_%H%M%S")
        filename = f"reporte_analisis_{timestamp}.pdf"
        full_path = os.path.join(PDF_DIR, filename)
        pdf.output(full_path)
        
        return filename