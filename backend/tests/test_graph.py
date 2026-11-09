"""Pruebas del modelo del grafo (models.py) y de la carga de datos (graph_service.py).

Ejecutar desde backend/:  pytest -v
"""
import json
import math
import tempfile
from pathlib import Path

import pytest

from app.graph_service import GraphDataError, get_graph, load_graph
from app.models import (
    DuplicateNodeError,
    Edge,
    Graph,
    GraphError,
    InvalidWeightError,
    Node,
    NodeNotFoundError,
)
from tests.helpers import make_small_graph


# ---------------------------------------------------------------------------
# Modelo: nodos y aristas
# ---------------------------------------------------------------------------
def test_agregar_y_consultar_nodo():
    g = Graph()
    g.add_node(Node("A", "Uno", 4.6, -74.0))
    assert g.has_node("A")
    assert g.get_node("A").name == "Uno"


def test_nodo_duplicado_se_rechaza():
    g = Graph()
    g.add_node(Node("A", "Uno", 4.6, -74.0))
    with pytest.raises(DuplicateNodeError):
        g.add_node(Node("A", "Otro", 4.7, -74.1))


def test_nodo_inexistente_lanza_error():
    g = make_small_graph()
    with pytest.raises(NodeNotFoundError):
        g.get_node("Z")
    with pytest.raises(NodeNotFoundError):
        g.neighbors("Z")


def test_arista_requiere_nodos_existentes():
    g = Graph()
    g.add_node(Node("A", "Uno", 4.6, -74.0))
    with pytest.raises(NodeNotFoundError):
        g.add_edge(Edge("A", "Z", 100, 10))


def test_nodo_con_datos_invalidos():
    with pytest.raises(GraphError):
        Node("", "Sin id", 4.6, -74.0)
    with pytest.raises(GraphError):
        Node("A", "Latitud imposible", 95.0, -74.0)



# Modelo: validación de pesos (Dijkstra exige pesos >= 0)

def test_duracion_negativa_se_rechaza():
    with pytest.raises(InvalidWeightError):
        Edge("A", "B", distance_meters=100, duration_seconds=-1)


def test_distancia_negativa_se_rechaza():
    with pytest.raises(InvalidWeightError):
        Edge("A", "B", distance_meters=-5, duration_seconds=10)


def test_peso_no_finito_se_rechaza():
    with pytest.raises(InvalidWeightError):
        Edge("A", "B", distance_meters=100, duration_seconds=math.inf)
    with pytest.raises(InvalidWeightError):
        Edge("A", "B", distance_meters=math.nan, duration_seconds=10)


def test_arista_a_si_mismo_se_rechaza():
    with pytest.raises(GraphError):
        Edge("A", "A", 100, 10)


# ---------------------------------------------------------------------------
# Modelo: el grafo es DIRIGIDO
# ---------------------------------------------------------------------------
def test_grafo_es_dirigido():
    g = make_small_graph()
    assert "B" in g.neighbors("A")        # existe A -> B
    assert "A" not in g.neighbors("B")    # pero NO existe B -> A


def test_aristas_asimetricas_conservan_su_propio_peso():
    g = make_small_graph()
    assert g.neighbors("A")["C"].duration_seconds == 500   # A -> C
    assert g.neighbors("C")["A"].duration_seconds == 50    # C -> A


def test_misma_conexion_reemplaza_a_la_anterior():
    g = make_small_graph()
    g.add_edge(Edge("A", "B", distance_meters=1, duration_seconds=1))
    assert g.neighbors("A")["B"].duration_seconds == 1
    assert len(g.neighbors("A")) == 2  # sigue siendo B y C, no se duplicó


# ---------------------------------------------------------------------------
# Carga desde JSON (graph_service.py)
# ---------------------------------------------------------------------------
def _cargar_texto(contenido: str) -> Graph:
    """Escribe `contenido` en un archivo temporal y lo carga como grafo."""
    with tempfile.TemporaryDirectory() as carpeta:
        archivo = Path(carpeta) / "grafo.json"
        archivo.write_text(contenido, encoding="utf-8")
        return load_graph(archivo)


def test_archivo_inexistente():
    with pytest.raises(GraphDataError):
        load_graph(Path("no_existe.json"))


def test_json_mal_formado():
    with pytest.raises(GraphDataError):
        _cargar_texto("{ esto no es json")


def test_falta_un_campo():
    # Al nodo le falta "lng".
    with pytest.raises(GraphDataError):
        _cargar_texto('{"nodes": [{"id": "A", "name": "x", "lat": 4.6}], "edges": []}')


def test_arista_hacia_nodo_inexistente():
    datos = {
        "nodes": [{"id": "A", "name": "x", "lat": 4.6, "lng": -74.0}],
        "edges": [{"origin": "A", "destination": "Z",
                   "distance_meters": 100, "duration_seconds": 10}],
    }
    with pytest.raises(GraphDataError):
        _cargar_texto(json.dumps(datos))


def test_peso_escrito_como_texto():
    datos = {
        "nodes": [{"id": "A", "name": "x", "lat": 4.6, "lng": -74.0},
                  {"id": "B", "name": "y", "lat": 4.7, "lng": -74.1}],
        "edges": [{"origin": "A", "destination": "B",
                   "distance_meters": "100", "duration_seconds": 10}],
    }
    with pytest.raises(GraphDataError):
        _cargar_texto(json.dumps(datos))


def test_peso_negativo_en_el_json():
    datos = {
        "nodes": [{"id": "A", "name": "x", "lat": 4.6, "lng": -74.0},
                  {"id": "B", "name": "y", "lat": 4.7, "lng": -74.1}],
        "edges": [{"origin": "A", "destination": "B",
                   "distance_meters": 100, "duration_seconds": -10}],
    }
    with pytest.raises(GraphDataError):
        _cargar_texto(json.dumps(datos))


# ---------------------------------------------------------------------------
# Datos reales (data/sample_graph.json)
# ---------------------------------------------------------------------------
def test_grafo_real_carga_16_nodos_y_68_aristas():
    g = get_graph()
    assert len(g.nodes()) == 16
    assert len(g.edges()) == 68


def test_grafo_real_tiene_pesos_positivos():
    for edge in get_graph().edges():
        assert edge.duration_seconds > 0
        assert edge.distance_meters > 0


def test_grafo_real_cada_conexion_tiene_su_sentido_inverso():
    # OSRM se consultó en ambos sentidos: si existe A -> C, debe existir C -> A.
    g = get_graph()
    for edge in g.edges():
        assert edge.origin in g.neighbors(edge.destination)
