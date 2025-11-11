from pymongo import MongoClient
from collections import Counter
import random
from datetime import datetime

# Conexión a MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["competition_manager"]

class reviewService:
    @staticmethod
    async def generar_reseñas_si_no_existen():
        """Genera reseñas aleatorias para todos los productos si no hay reseñas previas."""
        products = list(db.products.find())
        if db.reviews.count_documents({}) > 0:
            return {"message": "Ya existen reseñas en la base de datos."}

        comentarios = {
            "positive": [
                "Excelente calidad, totalmente recomendado.",
                "Cumple con lo prometido, muy buen producto.",
                "La batería dura bastante y el diseño es hermoso.",
                "Rendimiento excelente, vale la pena el precio.",
                "La cámara es increíble y muy fácil de usar."
            ],
            "neutral": [
                "Está bien por el precio, aunque esperaba más.",
                "Funciona correctamente, nada fuera de lo común.",
                "Buen producto, pero el envío tardó un poco.",
                "Aceptable, aunque podría mejorar el embalaje.",
                "Cumple su función básica sin destacar demasiado."
            ],
            "negative": [
                "Tuve problemas con la batería, no dura mucho.",
                "El producto llegó dañado, mala experiencia.",
                "No vale el precio, esperaba mejor rendimiento.",
                "El sonido es regular, esperaba más de la marca.",
                "Decepcionado, no lo volvería a comprar."
            ]
        }

        total_insertadas = 0
        for producto in products:
            reseñas = []
            for _ in range(random.randint(3, 10)):
                sentimiento = random.choice(["positive", "neutral", "negative"])
                comentario = random.choice(comentarios[sentimiento])
                rating = random.randint(1, 5)
                reseñas.append({
                    "product_id": str(producto["_id"]),
                    "brand": producto.get("brand", "Desconocida"),
                    "product_name": producto.get("name", "Sin nombre"),
                    "comment": comentario,
                    "rating": rating,
                    "sentiment": sentimiento,
                    "date": datetime.now().isoformat()
                })
            db.reviews.insert_many(reseñas)
            total_insertadas += len(reseñas)

        return {"message": f" {total_insertadas} reseñas generadas correctamente."}

    @staticmethod
    async def analizar_impacto(empresa: str, producto: str):
        """Analiza las reseñas de un producto específico."""
        filtro = {"brand": {"$regex": empresa, "$options": "i"}}
        if producto:
            filtro["product_name"] = {"$regex": producto, "$options": "i"}

        reseñas = list(db.reviews.find(filtro))
        if not reseñas:
            return {"message": f"No se encontraron reseñas para {producto} de {empresa}"}

        sentimientos = [r["sentiment"] for r in reseñas]
        conteo = Counter(sentimientos)
        total = len(sentimientos)

        # Resumen de porcentajes
        resumen = {
            "positive": round(conteo.get("positive", 0) / total * 100, 1),
            "neutral": round(conteo.get("neutral", 0) / total * 100, 1),
            "negative": round(conteo.get("negative", 0) / total * 100, 1),
            "total_reviews": total
        }

        if resumen["positive"] > resumen["negative"]:
            conclusion = f"🔹 El producto {producto} tiene una recepción general positiva."
        elif resumen["negative"] > resumen["positive"]:
            conclusion = f" El producto {producto} genera críticas mayormente negativas."
        else:
            conclusion = f" Las opiniones sobre {producto} están divididas."

        return {
            "empresa": empresa,
            "producto": producto,
            "resumen": resumen,
            "conclusion": conclusion,
            "reseñas_mostradas": reseñas[:5]  # solo mostrar 5 ejemplos
        }
