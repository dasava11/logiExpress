"""Pruebas de los endpoints (routes.py) con el cliente de pruebas de FastAPI.

Necesitan `httpx`, que ya está en requirements.txt.  Ejecutar desde backend/:  pytest -v
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.dijkstra import shortest_path
from app.graph_service import get_graph
from app.main import app
from tests.helpers import make_small_graph

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_locations_devuelve_16_ubicaciones():
    response = client.get("/api/locations")
    assert response.status_code == 200
    assert len(response.json()) == 16


def test_graph_devuelve_nodos_y_aristas():
    body = client.get("/api/graph").json()
    assert len(body["nodes"]) == 16
    assert len(body["edges"]) == 68


def test_ruta_simple():
    response = client.post("/api/routes/shortest-path", json={"origin": "A", "destination": "B"})
    assert response.status_code == 200
    body = response.json()
    assert body["algorithm"] == "Dijkstra"
    assert body["path"] == ["A", "J", "B"]
    assert body["total_duration_seconds"] == 1103
    # `nodes` trae las coordenadas en el mismo orden que `path`.
    assert [n["id"] for n in body["nodes"]] == body["path"]


def test_ruta_con_parada_intermedia_suma_los_dos_tramos():
    g = get_graph()
    tramo1 = shortest_path(g, "A", "E")
    tramo2 = shortest_path(g, "E", "G")

    response = client.post(
        "/api/routes/shortest-path",
        json={"origin": "A", "destination": "G", "stops": ["E"]},
    )
    body = response.json()

    assert response.status_code == 200
    # El nodo de unión (E) aparece una sola vez: no se repite entre tramos.
    assert body["path"] == tramo1.path + tramo2.path[1:]
    assert body["total_duration_seconds"] == (
        tramo1.total_duration_seconds + tramo2.total_duration_seconds
    )
    assert body["total_distance_meters"] == (
        tramo1.total_distance_meters + tramo2.total_distance_meters
    )


def test_nodo_inexistente_devuelve_400():
    response = client.post("/api/routes/shortest-path", json={"origin": "Z", "destination": "A"})
    assert response.status_code == 400


def test_parada_inexistente_devuelve_400():
    response = client.post(
        "/api/routes/shortest-path",
        json={"origin": "A", "destination": "B", "stops": ["Z"]},
    )
    assert response.status_code == 400


def test_sin_ruta_devuelve_404():
    # El grafo real es completamente conexo, así que se usa el pequeño
    # (en él D está aislado) reemplazando get_graph solo durante esta prueba.
    with patch("app.routes.get_graph", return_value=make_small_graph()):
        response = client.post("/api/routes/shortest-path", json={"origin": "A", "destination": "D"})
    assert response.status_code == 404


def test_solicitud_incompleta_devuelve_422():
    response = client.post("/api/routes/shortest-path", json={"origin": "A"})  # falta destination
    assert response.status_code == 422
