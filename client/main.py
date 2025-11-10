from fastapi import FastAPI
import uvicorn
from routers.modelRouter import modelRouter

app = FastAPI(title="Gestor de Competencia - Formosa", version="0.1.0")

app.include_router(modelRouter)

if __name__ == "__main__":
     uvicorn.run("main:app", port=6000,reload=True)