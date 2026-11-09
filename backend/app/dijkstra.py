"""Algoritmo de Dijkstra (implementación propia con heapq).

Responsabilidad: calcular el camino de menor duración entre dos nodos de un
`Graph`. No conoce FastAPI, React, Leaflet ni OSRM: recibe el grafo como dato.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass

from .models import Graph, GraphError


class NoPathError(GraphError):
    """El destino no es alcanzable desde el origen."""


@dataclass(frozen=True)
class ShortestPathResult:
    path: list[str]                # ids ordenados, origen -> destino
    total_duration_seconds: float  # costo minimizado por Dijkstra
    total_distance_meters: float   # métrica adicional del mismo camino
    examined_edges: int = 0        # cantidad de aristas examinadas durante la búsqueda.


def shortest_path(graph: Graph, origin: str, destination: str) -> ShortestPathResult:
    """Camino de menor duración de `origin` a `destination`.

    La idea en pocas palabras:
      1. Todos los nodos empiezan con costo "desconocido"; el origen tiene costo 0.
      2. Siempre se procesa el nodo pendiente con MENOR costo (lo da el heap).
      3. Al procesarlo, se mira cada vecino: si llegar por aquí es más barato
         que lo que se conocía, se actualiza su costo y se anota de dónde vino.
      4. Cuando sale del heap el destino, su costo ya no puede mejorar: se termina.
      5. Con las anotaciones de "de dónde vino" se reconstruye el camino al revés.

    Raises:
        NodeNotFoundError: si origen o destino no existen.
        NoPathError: si no hay camino dirigido entre ellos.

    Complejidad: O((V + E) log V). Cada arista se relaja como máximo una vez
    (E relajaciones) y cada inserción/extracción del heap cuesta O(log V).

    Los pesos no negativos los garantiza `Edge` al construirse; es lo que hace
    correcto a Dijkstra (con pesos negativos podría dar caminos erróneos).
    """
    # Validación de entrada: lanzan NodeNotFoundError si no existen.
    graph.get_node(origin)
    graph.get_node(destination)

    # Caso trivial: ya estamos en el destino.
    if origin == destination:
        return ShortestPathResult([origin], 0.0, 0.0)

    # --- Estructuras de trabajo -------------------------------------------
    distance: dict[str, float] = {origin: 0.0}  # mejor duración conocida hasta cada nodo
    previous: dict[str, str] = {}               # predecesor: "llegué a X viniendo de Y"
    visited: set[str] = set()                   # nodos con distancia ya definitiva
    # El heap es una cola de prioridad: heappop siempre entrega el elemento de
    # menor costo. Guardamos tuplas (costo, nodo); se comparan por costo primero.
    heap: list[tuple[float, str]] = [(0.0, origin)]

    examined_edges = 0  # contador de aristas examinadas durante la búsqueda

    # --- Bucle principal ----------------------------------------------------
    while heap:
        current_cost, node = heapq.heappop(heap)  # nodo pendiente más barato

        # Un nodo puede quedar repetido en el heap con costos viejos (más
        # altos). Si ya lo procesamos, esta entrada es obsoleta: se ignora.
        if node in visited:
            continue
        visited.add(node)

        # Si el nodo que sale es el destino, su costo ya es el mínimo.
        if node == destination:
            break

        # Relajación: probar cada arista de salida del nodo actual.
        for neighbor, edge in graph.neighbors(node).items():
            examined_edges += 1

            if neighbor in visited:
                continue

            new_cost = current_cost + edge.duration_seconds  # costo llegando por aquí
            # ¿Mejora lo que conocíamos? (math.inf = "aún no se ha llegado")
            if new_cost < distance.get(neighbor, math.inf):
                distance[neighbor] = new_cost
                previous[neighbor] = node  # anotamos de dónde venimos
                heapq.heappush(heap, (new_cost, neighbor))

    # Si el destino nunca salió del heap, no hay camino hasta él.
    if destination not in visited:
        raise NoPathError(f"No existe ruta de '{origin}' a '{destination}'.")

    path = _rebuild_path(previous, origin, destination)
    # Suma de distancias de cada arista del camino (zip junta pares consecutivos:
    # [A, C, P] -> (A, C), (C, P)).
    total_distance = sum(
        graph.neighbors(a)[b].distance_meters for a, b in zip(path, path[1:])
    )
    return ShortestPathResult(path, distance[destination], total_distance, examined_edges)


def _rebuild_path(previous: dict[str, str], origin: str, destination: str) -> list[str]:
    """Sigue los predecesores desde el destino hasta el origen y lo invierte."""
    path = [destination]
    while path[-1] != origin:
        path.append(previous[path[-1]])  # retrocede un paso
    path.reverse()  # se construyó destino -> origen; lo damos vuelta
    return path
