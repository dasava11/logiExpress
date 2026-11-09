"""Contratos Pydantic de la API (entrada y salida).

Pydantic revisa que los datos que llegan (y salen) tengan la forma correcta:
si falta un campo o el tipo es incorrecto, FastAPI responde 422 automáticamente.

Los nombres de campos coinciden con `models.py` y `dijkstra.py`.
Solo valida forma de los datos; la lógica de negocio vive en otros módulos.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


# --- Lo que el frontend ENVÍA -----------------------------------------------
class RouteRequest(BaseModel):
    origin: str = Field(min_length=1)       # id del origen, p. ej. "A"
    destination: str = Field(min_length=1)  # id del destino
    stops: list[str] = Field(default_factory=list)  # intermedios, en orden de visita


# --- Lo que el backend DEVUELVE ---------------------------------------------
# from_attributes=True permite crear estos modelos directamente desde los
# objetos Node y Edge de models.py (que no son diccionarios).
class NodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    lat: float
    lng: float


class EdgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    origin: str
    destination: str
    distance_meters: float
    duration_seconds: float


class GraphResponse(BaseModel):
    nodes: list[NodeOut]
    edges: list[EdgeOut]


class RouteSegmentOut(BaseModel):
    origin: str
    destination: str
    node_count: int
    examined_edges: int = Field(ge=0)


class RouteResponse(BaseModel):
    algorithm: str                  # siempre "Dijkstra"
    path: list[str]                 # ids en orden: origen ... destino
    total_duration_seconds: float
    total_distance_meters: float
    nodes: list[NodeOut]  # nodos de `path`, en el mismo orden (puede repetir ids)
    geometry: list[tuple[float, float]]  # trazado por calles, origen -> destino

    segments: list[RouteSegmentOut]
    total_examined_edges: int = Field(ge=0)