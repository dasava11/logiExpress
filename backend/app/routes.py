"""Endpoints HTTP. Orquesta graph_service y dijkstra; no contiene el algoritmo.

Un endpoint es una URL que el frontend puede llamar. Este archivo solo recibe
la petición, pide el cálculo a otros módulos y arma la respuesta.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .dijkstra import NoPathError, shortest_path
from .graph_service import get_graph
from .models import NodeNotFoundError
from .schemas import GraphResponse, NodeOut, RouteRequest, RouteResponse, RouteSegmentOut

# prefix="/api": todas las rutas de este archivo empiezan con /api
router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
    """Sirve para comprobar rápidamente que el backend está encendido."""
    return {"status": "ok"}


@router.get("/graph", response_model=GraphResponse)
def read_graph() -> GraphResponse:
    """Devuelve todos los nodos y todas las aristas del grafo."""
    graph = get_graph()
    return GraphResponse.model_validate({"nodes": graph.nodes(), "edges": graph.edges()})


@router.get("/locations", response_model=list[NodeOut])
def read_locations() -> list[NodeOut]:
    """Devuelve solo las ubicaciones; el frontend las usa en los selectores."""
    return [NodeOut.model_validate(n) for n in get_graph().nodes()]


@router.post("/routes/shortest-path", response_model=RouteResponse)
def calculate_route(request: RouteRequest) -> RouteResponse:
    """Dijkstra por cada tramo consecutivo: origen -> paradas (en orden) -> destino.

    El orden de las paradas es el que envía el usuario; no se optimiza
    (eso sería TSP y está fuera del alcance).
    """
    graph = get_graph()

    # Lista de puntos por los que hay que pasar, en orden.
    # Ejemplo: origen A, parada E, destino G -> ["A", "E", "G"]
    waypoints = [request.origin, *request.stops, request.destination]

    # zip(waypoints, waypoints[1:]) arma los tramos: (A, E) y (E, G).
    # Se ejecuta Dijkstra una vez por tramo.
    try:
        legs = [
            shortest_path(graph, a, b) 
            for a, b in zip(waypoints, waypoints[1:])
        ]
    except NodeNotFoundError as exc:  # el cliente envió un id que no existe
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NoPathError as exc:  # existe el nodo pero no hay camino hacia él
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # Une los caminos de cada tramo. Se omite el primer nodo de los tramos
    # siguientes porque ya es el último del tramo anterior.
    # Ej.: [A, C, P, E] + [E, F, G] -> [A, C, P, E, F, G]
    path = list(legs[0].path)
    for leg in legs[1:]:
        path.extend(leg.path[1:])

    # Une el trazado por calles de cada arista del camino.
    geometry: list[tuple[float, float]] = []
    for a, b in zip(path, path[1:]):
        points = graph.neighbors(a)[b].geometry
        # el primer punto de cada tramo repite el último del anterior
        geometry.extend(points if not geometry else points[1:])

    # Información individual de cada ejecución de Dijkstra.
    segments = [
        RouteSegmentOut(
            origin=origin,
            destination=destination,
            node_count=len(leg.path),
            examined_edges=leg.examined_edges,
        )
        for (origin, destination), leg in zip(
            zip(waypoints, waypoints[1:]),
            legs,
        )
    ]

    # Total de aristas examinadas en todos los tramos.
    total_examined_edges = sum(
        leg.examined_edges for leg in legs
    )

    # Construye la respuesta de la API.
    return RouteResponse(
        algorithm="Dijkstra",
        path=path,
        total_duration_seconds=sum(
            leg.total_duration_seconds for leg in legs
        ),
        total_distance_meters=sum(
            leg.total_distance_meters for leg in legs
        ),
        nodes=[
            NodeOut.model_validate(graph.get_node(node_id))
            for node_id in path
        ],
        geometry=geometry,
        segments=segments,
        total_examined_edges=total_examined_edges,
    )

