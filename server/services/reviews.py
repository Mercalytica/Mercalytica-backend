# services/reviews.py
class ReviewsServicer:
    def __init__(self, connector):
        self.connector = connector
        self.collection_name = "reviews"

    async def summary_by_product(self, brand: str, product_name: str):
        """Resumen agregado de reseñas por producto y marca."""
        pipeline = [
            { "$match": {
                "brand": { "$regex": f"^{brand}$", "$options": "i" },
                "product_name": { "$regex": f"^{product_name}$", "$options": "i" }
            }},
            { "$group": {
                "_id": "$product_name",
                "total_reviews": { "$sum": 1 },
                "positive": { "$sum": { "$cond": [{ "$eq": ["$sentiment", "positive"] }, 1, 0] } },
                "neutral": { "$sum": { "$cond": [{ "$eq": ["$sentiment", "neutral"] }, 1, 0] } },
                "negative": { "$sum": { "$cond": [{ "$eq": ["$sentiment", "negative"] }, 1, 0] } },
            }}
        ]
        result = await self.connector.aggregate(self.collection_name, pipeline)
        return result[0] if result else None

    async def reviews_by_product(self, brand: str, product_name: str, limit: int = 50):
        """Trae reseñas individuales por producto y marca."""
        query = {
            "brand": { "$regex": f"^{brand}$", "$options": "i" },
            "product_name": { "$regex": f"^{product_name}$", "$options": "i" }
        }
        cursor = self.connector.db[self.collection_name].find(query).sort("date", -1).limit(limit)
        result = await cursor.to_list(length=limit)
        return result

    async def analizar_impacto(self, brand: str, product_name: str):
        """Combina resumen y reseñas individuales para un producto."""
        resumen = await self.summary_by_product(brand, product_name)
        reseñas = await self.reviews_by_product(brand, product_name)

        if not resumen:
            return {"reseñas_mostradas": False}

        conclusion = f"Se analizaron {resumen['total_reviews']} reseñas de {product_name}. "
        mayor_sentimiento = max(['positive', 'neutral', 'negative'], key=lambda x: resumen[x])
        conclusion += f"La mayoría de los comentarios son {mayor_sentimiento}."

        return {
            "reseñas_mostradas": True,
            "reseñas": reseñas[:10],  # primeras 10
            "resumen": resumen,
            "conclusion": conclusion
        }
