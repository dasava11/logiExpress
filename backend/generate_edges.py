"""Genera las aristas del grafo consultando OSRM (servicio público de rutas).

Para cada conexión de CONNECTIONS se pide a OSRM la ruta en AMBOS sentidos y se
guarda: distancia (m), duración (s) y el trazado por calles (lista de puntos).

Uso, desde la carpeta backend/ y con conexión a internet:
    python generate_edges.py        (en Windows también: py generate_edges.py)

Qué hace con los archivos:
  1. Lee los nodos de data/sample_graph.json.
  2. Escribe todas las aristas en data/edges_generated.json (registro).
  3. Si se obtuvieron TODAS las aristas (2 por conexión), guarda una copia de
     seguridad (data/sample_graph.backup.json) y actualiza las aristas de
     data/sample_graph.json. Si faltó alguna, NO toca sample_graph.json.
"""
import json
import shutil
import time
from pathlib import Path

import httpx


DATA_FILE = Path("data/sample_graph.json")
OUTPUT_FILE = Path("data/edges_generated.json")
BACKUP_FILE = Path("data/sample_graph.backup.json")

# Conexiones candidatas del grafo.
CONNECTIONS = [
    ("A", "C"),
    ("A", "J"),
    ("A", "L"),
    ("B", "J"),
    ("B", "I"),
    ("B", "O"),
    ("C", "P"),
    ("C", "I"),
    ("D", "E"),
    ("D", "N"),
    ("D", "P"),
    ("E", "M"),
    ("F", "H"),
    ("F", "L"),
    ("G", "N"),
    ("G", "I"),
    ("H", "O"),
    ("H", "L"),
    ("I", "J"),
    ("I", "K"),
    ("J", "K"),
    ("K", "O"),
    ("L", "M"),
    ("P", "E"),
    ("A", "O"),
    ("C", "N"),
    ("C", "O"),
    ("D", "G"),
    ("D", "F"),
    ("F", "P"),
    ("H", "K"),
    ("L", "P"),
    ("M", "N"),
    ("H", "M"),
]

BASE_URL = "https://router.project-osrm.org/route/v1/driving"


def build_edge(origin, destination, route):
    """Convierte la respuesta de OSRM en una arista de nuestro grafo."""

    # OSRM entrega cada punto como [longitud, latitud]; nuestro JSON usa
    # [latitud, longitud] (el orden que espera Leaflet). Se redondea a 5
    # decimales (~1 metro) para que el archivo no pese demasiado.
    geometry = [
        [round(lat, 5), round(lng, 5)]
        for lng, lat in route["geometry"]["coordinates"]
    ]

    return {
        "origin": origin,
        "destination": destination,
        "distance_meters": round(route["distance"]),
        "duration_seconds": round(route["duration"]),
        "geometry": geometry,
    }


def get_route(client, origin, destination, nodes):
    """Consulta distancia, duración y trazado de una conexión vial."""

    start = nodes[origin]
    end = nodes[destination]

    coordinates = (
        f"{start['lng']},{start['lat']};"
        f"{end['lng']},{end['lat']}"
    )

    url = f"{BASE_URL}/{coordinates}"

    response = client.get(
        url,
        params={
            "overview": "full",       # trazado completo de la ruta
            "geometries": "geojson",  # puntos como [lng, lat]
            "steps": "false",
        }
    )

    response.raise_for_status()
    result = response.json()

    if result["code"] != "Ok" or not result["routes"]:
        print(f"Sin ruta: {origin} -> {destination}")
        return None

    return build_edge(origin, destination, result["routes"][0])


def save_json(path, sections):
    """Guarda un JSON legible: cada nodo/arista en su propia línea.

    `sections` es un diccionario {"nodes": [...], "edges": [...]}. Con
    json.dump(indent=2) cada coordenada de la geometría quedaría en una línea
    distinta y el archivo sería ilegible.
    """
    lines = ["{"]
    names = list(sections)
    for number, name in enumerate(names):
        items = sections[name]
        lines.append(f'  "{name}": [')
        for i, item in enumerate(items):
            comma = "," if i < len(items) - 1 else ""
            lines.append("    " + json.dumps(item, ensure_ascii=False) + comma)
        lines.append("  ]" + ("," if number < len(names) - 1 else ""))
    lines.append("}")

    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        graph_data = json.load(file)

    nodes = {
        node["id"]: node
        for node in graph_data["nodes"]
    }

    edges = []

    with httpx.Client(timeout=30) as client:

        for origin, destination in CONNECTIONS:

            try:
                # Consultar ambos sentidos.
                for start, end in [
                    (origin, destination),
                    (destination, origin)
                ]:
                    edge = get_route(
                        client, start, end, nodes
                    )

                    if edge:
                        edges.append(edge)
                        print(
                            f"{start} -> {end}: "
                            f"{edge['distance_meters']} m, "
                            f"{len(edge['geometry'])} puntos"
                        )

                    # Uso moderado del servicio público.
                    time.sleep(1)

            except httpx.HTTPError as error:
                print(
                    f"Error {origin} -> {destination}: {error}"
                )

    save_json(OUTPUT_FILE, {"edges": edges})

    expected = len(CONNECTIONS) * 2
    print(f"\nTotal de aristas generadas: {len(edges)} de {expected}")
    print(f"Archivo generado: {OUTPUT_FILE}")

    if len(edges) == expected:
        shutil.copyfile(DATA_FILE, BACKUP_FILE)
        save_json(DATA_FILE, {"nodes": graph_data["nodes"], "edges": edges})
        print(f"Grafo actualizado: {DATA_FILE} (copia anterior en {BACKUP_FILE})")
    else:
        print(
            "Faltaron aristas, así que NO se modificó "
            f"{DATA_FILE}. Revisa los avisos de arriba y vuelve a ejecutar."
        )


if __name__ == "__main__":
    main()
