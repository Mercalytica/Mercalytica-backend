from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routers.modelRouter import modelRouter, reviewRouter

app = FastAPI(title="Gestor de Competencia - Formosa", version="0.1.0")

# 🌐 Configuración de CORS
origins = [
    "http://localhost:5173",   # frontend local (Vite)
    "http://127.0.0.1:5173",
    # podés agregar más dominios si desplegás el frontend
    # "https://mercalytica.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],        # permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],        # permite todos los encabezados
)

app.include_router(modelRouter)
app.include_router(reviewRouter)

if __name__ == "__main__":
     uvicorn.run("main:app", port=5001,reload=True)