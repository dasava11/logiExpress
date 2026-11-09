"""Grafo pequeño para las pruebas. Es independiente de los datos reales.

Así las pruebas no se rompen si cambian los pesos de sample_graph.json.

    A --B--> (100 s, 1000 m)       A -> C directa: 500 s pero solo 800 m
    B --C--> (100 s, 1000 m)       C -> A directa: 50 s (asimetría)
    D: nodo aislado                E: solo tiene salida (E -> A)
"""
from app.models import Edge, Graph, Node


def make_small_graph() -> Graph:
    g = Graph()
    for node_id in "ABCDE":
        g.add_node(Node(node_id, f"Nodo {node_id}", 4.6, -74.0))
    g.add_edge(Edge("A", "B", distance_meters=1000, duration_seconds=100))
    g.add_edge(Edge("B", "C", distance_meters=1000, duration_seconds=100))
    g.add_edge(Edge("A", "C", distance_meters=800, duration_seconds=500))
    g.add_edge(Edge("C", "A", distance_meters=800, duration_seconds=50))
    g.add_edge(Edge("E", "A", distance_meters=300, duration_seconds=30))
    return g
