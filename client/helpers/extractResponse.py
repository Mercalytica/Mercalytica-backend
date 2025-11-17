from typing import Any, Dict, Union, List

def extraer_respuesta_aimessage(respuesta_modelo: Union[Dict[str, Any], Any]) -> str:
    """
    Interpreta un objeto de respuesta del modelo (AIMessage o diccionario) 
    y extrae el contenido de texto, manejando múltiples formatos posibles.
    """
    
    try:
        contenido = None
        
        # 1. Si es un diccionario con 'content'
        if isinstance(respuesta_modelo, dict):
            if 'content' in respuesta_modelo:
                contenido = respuesta_modelo['content']
            elif 'message' in respuesta_modelo:
                contenido = respuesta_modelo['message']
            elif 'text' in respuesta_modelo:
                contenido = respuesta_modelo['text']
        
        # 2. Si es un objeto con atributo 'content'
        elif hasattr(respuesta_modelo, 'content'):
            contenido = respuesta_modelo.content
        
        # 3. Si es una cadena directa
        elif isinstance(respuesta_modelo, str):
            return respuesta_modelo
        
        # Procesar el contenido extraído
        if contenido is not None:
            
            # Si el contenido es una lista
            if isinstance(contenido, list) and len(contenido) > 0:
                primer_elemento = contenido[0]
                
                # Si el primer elemento es un diccionario con 'text'
                if isinstance(primer_elemento, dict):
                    if 'text' in primer_elemento:
                        return str(primer_elemento['text']).strip()
                    elif 'message' in primer_elemento:
                        return str(primer_elemento['message']).strip()
                    else:
                        # Si es un dict, intentar obtener el primer valor
                        valores = list(primer_elemento.values())
                        if valores:
                            return str(valores[0]).strip()
                
                # Si el primer elemento es una cadena
                return str(primer_elemento).strip()
            
            # Si el contenido es una cadena simple
            elif isinstance(contenido, str):
                return contenido.strip()
            
            # Si el contenido es un número u otro tipo
            elif contenido is not None:
                return str(contenido).strip()
        
        # Fallback final
        return f"Error: No se pudo extraer el contenido. Tipo recibido: {type(respuesta_modelo).__name__}"
        
    except Exception as e:
        return f"Error extrayendo respuesta: {str(e)}"