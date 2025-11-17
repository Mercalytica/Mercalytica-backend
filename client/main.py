from fastapi import FastAPI
import uvicorn
from routers.modelRouter import modelRouter
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.cors import CORSMiddleware


app = FastAPI(title="Gestor de Competencia - Formosa", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(modelRouter)

if __name__ == "__main__":
     uvicorn.run("main:app", host="0.0.0.0",port=5000,reload=True)