"""Verifica el grafo ampliado (32 conexiones / 64 aristas dirigidas).

Uso, desde la carpeta backend/:   python verify_graph.py
Lee data/sample_graph.json. No modifica nada.
"""
import json
from collections import deque
from pathlib import Path

FILE = Path("data/sample_graph.json")
NUEVAS = [("A", "O"), ("C", "N"), ("C", "O"), ("D", "G"), ("D", "F"), ("F", "P"), ("H", "K"), ("L", "P")]
# Peso ESTIMADO (s) de cada conexión nueva, para compararlo con lo que devuelva OSRM.
ESTIMADO = {("A", "O"): 949, ("C", "N"): 1015, ("C", "O"): 839, ("D", "G"): 999,
            ("D", "F"): 1576, ("F", "P"): 1219, ("H", "K"): 1171, ("L", "P"): 1094}

data = json.loads(FILE.read_text(encoding="utf-8"))
nodes = {n["id"] for n in data["nodes"]}
edges = data["edges"]
pairs = [(e["origin"], e["destination"]) for e in edges]
pair_set = set(pairs)
fallos = 0


def check(texto, ok):
    global fallos
    print(("✔ " if ok else "✘ ") + texto)
    fallos += not ok


check(f"16 nodos (hay {len(nodes)})", len(nodes) == 16)
check(f"64 aristas dirigidas (hay {len(edges)})", len(edges) == 64)
check("sin aristas duplicadas", len(pair_set) == len(pairs))
conexiones = {frozenset(p) for p in pairs}
check(f"32 conexiones (hay {len(conexiones)})", len(conexiones) == 32)
check("cada conexión existe en ambos sentidos", all((b, a) in pair_set for a, b in pairs))
check("todos los extremos son nodos válidos", all(a in nodes and b in nodes for a, b in pairs))
check("sin aristas de un nodo hacia sí mismo", all(a != b for a, b in pairs))
check("distancia y duración > 0 en todas", all(e["distance_meters"] > 0 and e["duration_seconds"] > 0 for e in edges))
check("todas las aristas traen geometry (≥ 2 puntos)", all(len(e.get("geometry", [])) >= 2 for e in edges))
check("las 8 conexiones nuevas están", all((a, b) in pair_set and (b, a) in pair_set for a, b in NUEVAS))


def alcanzables(inicio, vecinos):
    visto, cola = {inicio}, deque([inicio])
    while cola:
        for m in vecinos[cola.popleft()]:
            if m not in visto:
                visto.add(m)
                cola.append(m)
    return visto


ady = {n: [] for n in nodes}
rev = {n: [] for n in nodes}
for a, b in pairs:
    ady[a].append(b)
    rev[b].append(a)
inicio = sorted(nodes)[0]
check("grafo fuertemente conexo (240 pares con ruta)",
      alcanzables(inicio, ady) == nodes and alcanzables(inicio, rev) == nodes)

grado = {n: len(ady[n]) for n in sorted(nodes)}
print("\nConexiones por nodo:", grado)

por_par = {(e["origin"], e["destination"]): e for e in edges}
print("\nConexiones nuevas: peso estimado vs OSRM (segundos)")
for a, b in NUEVAS:
    if (a, b) in por_par:
        real = (por_par[(a, b)]["duration_seconds"], por_par[(b, a)]["duration_seconds"])
        print(f"  {a}-{b}: estimado {ESTIMADO[(a, b)]:>5} | OSRM {a}->{b} {real[0]:>5}, {b}->{a} {real[1]:>5}")

print("\nRESULTADO:", "todo correcto" if not fallos else f"{fallos} comprobación(es) fallida(s)")
