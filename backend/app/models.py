"""Modelos del grafo dirigido de LogiExpress.

Acá se define:
  * Node  -> una ubicación (vertice).
  * Edge  -> una conexión de un nodo a otro, con distancia y duración (arista con peso).
  * Graph -> guarda todos los nodos y, para cada uno, sus aristas de salida.

El grafo es DIRIGIDO: una calle de doble sentido son dos aristas (A->B y B->A),
porque la ida y la vuelta pueden tener distinta distancia o tiempo, basados en los sentidos recorrido vial.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


# Errores propios. Todos heredan de GraphError, así otros archivos pueden
# capturar "cualquier error del grafo" o uno específico.

class GraphError(Exception):
    """Error base de dominio para todo lo relacionado con el grafo."""


class DuplicateNodeError(GraphError):
    """Se intento registrar dos nodos con el mismo id."""


class NodeNotFoundError(GraphError):
    """Se consulto un nodo que no existe en el grafo."""


class InvalidWeightError(GraphError):
    """Un peso (distancia o duración) es negativo o no es un numero finito."""


# frozen=True: una vez creado, el objeto no se puede modificar. Evita que
# en alguna parte del flujo se cambie por accidente los datos de un nodo en medio del calculo.
@dataclass(frozen=True)
class Node:
    """Ubicación del mapa. `id` es el identificador estable (ej. "A")."""

    id: str
    name: str
    lat: float
    lng: float

    # __post_init__ se ejecuta automáticamente justo después de crear el objeto.
    # Lo usamos para rechazar datos inválidos desde el principio.
    def __post_init__(self) -> None:
        if not self.id:
            raise GraphError("El id del nodo no puede estar vacío.")
        if not (-90 <= self.lat <= 90 and -180 <= self.lng <= 180):
            raise GraphError(f"Coordenadas fuera de rango en el nodo '{self.id}'.")


@dataclass(frozen=True)
class Edge:
    """Conexión dirigida origin -> destination.

    El peso que usa Dijkstra es `duration_seconds`; `distance_meters` se
    conserva como métrica adicional. Ambos deben ser >= 0.
    """

    origin: str
    destination: str
    distance_meters: float
    duration_seconds: float
    geometry: tuple[tuple[float, float], ...] = ()  # (lat, lng) por calles

    def __post_init__(self) -> None:
        # Una arista de un nodo hacia sí mismo no tiene sentido en una ruta.
        if self.origin == self.destination:
            raise GraphError(f"Arista inválida: '{self.origin}' se conecta consigo mismo.")
        # Dijkstra solo funciona bien con pesos >= 0, por eso se validan aquí,
        # una sola vez, en lugar de revisarlos dentro del algoritmo.
        for label, value in (
            ("distance_meters", self.distance_meters),
            ("duration_seconds", self.duration_seconds),
        ):
            if not math.isfinite(value) or value < 0:
                raise InvalidWeightError(
                    f"{label} debe ser un número finito >= 0 "
                    f"(arista {self.origin}->{self.destination}, valor {value})."
                )


class Graph:
    """Grafo dirigido con lista de adyacencia basada en diccionarios.

    Forma interna (ejemplo):

        _nodes     = {"A": Node(...), "B": Node(...), ...}
        _adjacency = {"A": {"C": Edge(A->C), "J": Edge(A->J), "L": Edge(A->L)},
                      "B": {"J": Edge(B->J), "I": Edge(B->I), "O": Edge(B->O)},
                      ...}

    Es decir: para cada nodo guardamos solo SUS vecinos de salida. Por eso:
      * consultar los vecinos de u cuesta O(grado de salida de u), sin recorrer
        todas las aristas del grafo;
      * saber si existe u->v y obtener sus pesos es O(1) promedio;
      * el espacio es O(V + E), adecuado para grafos dispersos (una matriz
        de adyacencia usaría O(V²)).

    Si se agrega dos veces la misma conexión u->v, la última reemplaza a la
    anterior.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}              # id -> Node
        self._adjacency: dict[str, dict[str, Edge]] = {}  # id -> {id_vecino: Edge}

    def add_node(self, node: Node) -> None:
        if node.id in self._nodes:
            raise DuplicateNodeError(f"Ya existe un nodo con id '{node.id}'.")
        self._nodes[node.id] = node
        self._adjacency[node.id] = {}  # empieza sin aristas de salida

    def add_edge(self, edge: Edge) -> None:
        # Ambos extremos deben existir; si no, _require lanza NodeNotFoundError.
        self._require(edge.origin)
        self._require(edge.destination)
        self._adjacency[edge.origin][edge.destination] = edge

    def has_node(self, node_id: str) -> bool:
        return node_id in self._nodes

    def get_node(self, node_id: str) -> Node:
        self._require(node_id)
        return self._nodes[node_id]

    def neighbors(self, node_id: str) -> Mapping[str, Edge]:
        """Aristas de salida de `node_id` como {id_vecino: Edge} (solo lectura)."""
        self._require(node_id)
        # MappingProxyType entrega una vista de solo lectura: quien llame no
        # puede modificar por accidente la lista de adyacencia interna.
        return MappingProxyType(self._adjacency[node_id])

    def nodes(self) -> list[Node]:
        return list(self._nodes.values())

    def edges(self) -> list[Edge]:
        # Junta las aristas de salida de todos los nodos en una sola lista.
        return [e for out in self._adjacency.values() for e in out.values()]

    def _require(self, node_id: str) -> None:
        """Método interno: lanza error claro si el nodo no existe."""
        if node_id not in self._nodes:
            raise NodeNotFoundError(f"El nodo '{node_id}' no existe en el grafo.")


if __name__ == "__main__":  # Ejemplo breve de uso: python -m app.models
    g = Graph()
    g.add_node(Node("A", "Bodega", 4.6097, -74.0817))
    g.add_node(Node("B", "Norte", 4.6500, -74.0600))
    g.add_edge(Edge("A", "B", distance_meters=4000, duration_seconds=600))  # solo A->B
    print(dict(g.neighbors("A")))  # {'B': Edge(...)}
    print(dict(g.neighbors("B")))  # {} : B no tiene salidas
