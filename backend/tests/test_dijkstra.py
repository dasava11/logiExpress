"""Pruebas del algoritmo de Dijkstra (dijkstra.py).

Primero se prueba con un grafo pequeño (cuyos resultados se calculan a mano) y
al final con los datos reales.  Ejecutar desde backend/:  pytest -v
"""
import itertools

import pytest

from app.dijkstra import NoPathError, shortest_path
from app.graph_service import get_graph
from app.models import NodeNotFoundError
from tests.helpers import make_small_graph


# ---------------------------------------------------------------------------
# Casos básicos (grafo pequeño de tests/helpers.py)
# ---------------------------------------------------------------------------
def test_ruta_directa_cuando_es_la_mas_barata():
    r = shortest_path(make_small_graph(), "B", "C")
    assert r.path == ["B", "C"]
    assert r.total_duration_seconds == 100
    assert r.total_distance_meters == 1000


def test_ruta_alternativa_cuando_es_mas_rapida():
    # A -> C directo cuesta 500 s; A -> B -> C cuesta 100 + 100 = 200 s.
    r = shortest_path(make_small_graph(), "A", "C")
    assert r.path == ["A", "B", "C"]
    assert r.total_duration_seconds == 200


def test_minimiza_duracion_no_distancia():
    # El camino directo es MÁS CORTO en metros (800 contra 2000),
    # pero Dijkstra optimiza segundos, así que elige el otro.
    r = shortest_path(make_small_graph(), "A", "C")
    assert r.total_distance_meters == 2000  # la distancia solo se acumula como métrica


def test_origen_igual_a_destino():
    r = shortest_path(make_small_graph(), "A", "A")
    assert r.path == ["A"]
    assert r.total_duration_seconds == 0
    assert r.total_distance_meters == 0


def test_aristas_asimetricas():
    g = make_small_graph()
    assert shortest_path(g, "A", "C").total_duration_seconds == 200  # ida: por B
    assert shortest_path(g, "C", "A").total_duration_seconds == 50   # vuelta: directa


def test_el_grafo_es_dirigido_en_el_algoritmo():
    g = make_small_graph()
    assert shortest_path(g, "E", "A").path == ["E", "A"]  # E -> A existe
    with pytest.raises(NoPathError):
        shortest_path(g, "A", "E")                        # A -> E no existe


# ---------------------------------------------------------------------------
# Errores controlados
# ---------------------------------------------------------------------------
def test_destino_aislado_no_tiene_ruta():
    with pytest.raises(NoPathError):
        shortest_path(make_small_graph(), "A", "D")


def test_origen_inexistente():
    with pytest.raises(NodeNotFoundError):
        shortest_path(make_small_graph(), "Z", "A")


def test_destino_inexistente():
    with pytest.raises(NodeNotFoundError):
        shortest_path(make_small_graph(), "A", "Z")


# ---------------------------------------------------------------------------
# Comprobación contra fuerza bruta (solo grafo pequeño)
# ---------------------------------------------------------------------------
def _menor_costo_por_fuerza_bruta(graph, origen, destino):
    """Prueba TODOS los caminos sin repetir nodos y devuelve el menor costo."""
    mejor = None

    def explorar(nodo, visitados, costo):
        nonlocal mejor
        if nodo == destino:
            if mejor is None or costo < mejor:
                mejor = costo
            return
        for vecino, arista in graph.neighbors(nodo).items():
            if vecino not in visitados:
                explorar(vecino, visitados | {vecino}, costo + arista.duration_seconds)

    explorar(origen, {origen}, 0)
    return mejor


def test_coincide_con_fuerza_bruta_en_todos_los_pares():
    g = make_small_graph()
    ids = [n.id for n in g.nodes()]
    for origen, destino in itertools.permutations(ids, 2):
        esperado = _menor_costo_por_fuerza_bruta(g, origen, destino)
        if esperado is None:
            with pytest.raises(NoPathError):
                shortest_path(g, origen, destino)
        else:
            assert shortest_path(g, origen, destino).total_duration_seconds == esperado


# ---------------------------------------------------------------------------
# Datos reales (16 nodos de Bogotá, pesos de OSRM)
# ---------------------------------------------------------------------------
def test_real_ruta_conocida_A_a_B():
    # Universidad EAN -> Plaza de Bolívar: no hay arista directa; el mejor camino pasa por J.
    r = shortest_path(get_graph(), "A", "B")
    assert r.path == ["A", "J", "B"]
    assert r.total_duration_seconds == 805 + 298
    assert r.total_distance_meters == 7131 + 1947


def test_real_todos_los_pares_tienen_ruta_y_los_totales_son_la_suma_de_sus_aristas():
    g = get_graph()
    ids = [n.id for n in g.nodes()]
    for origen, destino in itertools.permutations(ids, 2):
        r = shortest_path(g, origen, destino)
        assert r.path[0] == origen and r.path[-1] == destino
        tramos = list(zip(r.path, r.path[1:]))
        # Cada par consecutivo del camino debe ser una arista que de verdad existe.
        assert sum(g.neighbors(a)[b].duration_seconds for a, b in tramos) == r.total_duration_seconds
        assert sum(g.neighbors(a)[b].distance_meters for a, b in tramos) == r.total_distance_meters


def test_real_optimalidad_ninguna_arista_mejora_un_costo():
    # Si Dijkstra fuera incorrecto, existiría alguna arista u -> v tal que
    # costo(origen, u) + peso(u -> v) < costo(origen, v). Se comprueba que no ocurre.
    g = get_graph()
    ids = [n.id for n in g.nodes()]
    for origen in ids:
        costo = {d: shortest_path(g, origen, d).total_duration_seconds for d in ids}
        for e in g.edges():
            assert costo[e.destination] <= costo[e.origin] + e.duration_seconds
