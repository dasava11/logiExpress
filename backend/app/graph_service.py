"""Carga y acceso al grafo.

Responsabilidad: leer `data/sample_graph.json`, construir un `Graph` con los
modelos de models.py y entregarlo al resto de la aplicación. No implementa
Dijkstra ni duplica la validación de `models.py`.

Formato esperado del JSON (una sola fuente de datos: nodos y aristas juntos):
{
  "nodes": [{"id": "A", "name": "...", "lat": 4.6, "lng": -74.0}],
  "edges": [{"origin": "A", "destination": "B",
             "distance_meters": 4000, "duration_seconds": 600}]
}
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .models import Edge, Graph, GraphError, Node

# Ruta del JSON calculada a partir de la ubicación de este archivo, así
# funciona sin importar desde qué carpeta se ejecute el servidor.
DEFAULT_GRAPH_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_graph.json"


class GraphDataError(GraphError):
    """El archivo del grafo no existe, no es JSON válido o tiene datos incorrectos."""


def load_graph(path: Path = DEFAULT_GRAPH_PATH) -> Graph:
    """Construye un Graph desde un archivo JSON."""
    # Paso 1: leer el archivo y convertirlo a diccionarios de Python.
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise GraphDataError(f"No se encontró el archivo del grafo: {path}") from None
    except json.JSONDecodeError as exc:
        raise GraphDataError(f"JSON inválido en {path}: {exc}") from exc

    # Paso 2: crear primero los nodos y después las aristas (una arista
    # necesita que sus dos nodos ya existan).
    graph = Graph()
    try:
        for item in raw["nodes"]:
            graph.add_node(Node(item["id"], item["name"], item["lat"], item["lng"]))
        for item in raw["edges"]:
            graph.add_edge(
                Edge(
                    item["origin"],
                    item["destination"],
                    item["distance_meters"],
                    item["duration_seconds"],
                    tuple((p[0], p[1]) for p in item.get("geometry", [])),
                )
            )
    except KeyError as exc:  # falta un campo en el JSON
        raise GraphDataError(f"Falta el campo {exc} en {path}.") from exc
    except TypeError as exc:  # un número escrito como texto, p. ej. "500" en vez de 500
        raise GraphDataError(f"Tipo de dato incorrecto en {path}: {exc}") from exc
    except GraphError as exc:  # ids duplicados, aristas a nodos inexistentes, pesos negativos
        raise GraphDataError(f"Datos de grafo inválidos en {path}: {exc}") from exc
    return graph


# lru_cache(maxsize=1): la primera llamada carga el grafo y guarda el
# resultado; las siguientes lo devuelven sin volver a leer el archivo.
@lru_cache(maxsize=1)
def get_graph() -> Graph:
    """Grafo compartido por la aplicación; se carga una sola vez."""
    return load_graph()
