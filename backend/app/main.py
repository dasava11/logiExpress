"""Punto de entrada FastAPI. Sin lógica de negocio.

Aquí solo se crea la aplicación, se configura CORS y se registran los endpoints.

Ejecutar desde la carpeta backend/:
    uvicorn app.main:app --reload --port 8000
Documentación interactiva (Swagger): http://localhost:8000/docs
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .graph_service import get_graph
from .routes import router

# CORS: el navegador bloquea que una página de un origen (el frontend, en el
# puerto de Vite) llame a otro origen (este backend, puerto 8000) salvo que el
# backend lo autorice. Aquí se listan los orígenes permitidos.
# Vite usa 5173 y, si está ocupado, prueba 5174, 5175, etc.
# Conviene dejar solo los puertos que realmente se usen.
FRONTEND_ORIGINS = [
    "http://localhost:5173", 
    "http://localhost:5174", 
    "http://localhost:5175", 
    "http://localhost:5176", 
    "http://localhost:5177", 
    "http://localhost:5178", 
    "http://localhost:5179", 
    "http://localhost:5180", 
    "http://127.0.0.1:5173"
    ]  # Vite dev


# lifespan: código que corre al arrancar y al apagar el servidor.
@asynccontextmanager
async def lifespan(_: FastAPI):
    get_graph()  # falla al arrancar si el JSON del grafo es inválido
    yield        # a partir de aquí el servidor atiende peticiones


app = FastAPI(title="LogiExpress API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(router)  # registra los endpoints de routes.py
