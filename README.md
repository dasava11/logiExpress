# LogiExpress

Herramienta local de **cálculo de rutas de entrega** sobre un grafo dirigido de 16 ubicaciones de Bogotá. Proyecto final de _Estructuras de Datos_.

El usuario elige un origen, un destino y, opcionalmente, paradas intermedias. El backend calcula el camino de **menor duración** con un **algoritmo de Dijkstra implementado a mano** y el frontend muestra el resultado en un mapa.

> **Principio de diseño:** el cálculo vive solo en Python. React y el mapa únicamente visualizan lo que el backend devuelve.

---

## Guía rápida

Si ya tienes Python y Node instalados, estos son los comandos mínimos. Cada paso se explica más abajo.

| Paso                                    | macOS                                         | Windows (PowerShell)                          |
| --------------------------------------- | --------------------------------------------- | --------------------------------------------- |
| 1. Entrar al backend                    | `cd backend`                                  | `cd backend`                                  |
| 2. Crear entorno virtual (una sola vez) | `python3 -m venv venv`                        | `py -m venv venv`                             |
| 3. Activarlo                            | `source venv/bin/activate`                    | `.\venv\Scripts\Activate.ps1`                 |
| 4. Instalar dependencias (una sola vez) | `pip install -r requirements.txt`             | `pip install -r requirements.txt`             |
| 5. Levantar el backend                  | `uvicorn app.main:app --reload --port 8000`   | `uvicorn app.main:app --reload --port 8000`   |
| 6. (Otra terminal) Levantar el frontend | `cd frontend` → `npm install` → `npm run dev` | `cd frontend` → `npm install` → `npm run dev` |
| 7. Abrir                                | `http://localhost:5173`                       | `http://localhost:5173`                       |
| Pruebas                                 | `cd backend` → `pytest -v`                    | `cd backend` → `pytest -v`                    |

## Contenido

- [¿Cómo funciona?](#cómo-funciona)
- [Estado del proyecto](#estado-del-proyecto)
- [Arquitectura](#arquitectura)
- [Estructura de carpetas](#estructura-de-carpetas)
- [Los datos: ubicaciones y conexiones](#los-datos-ubicaciones-y-conexiones)
- [Requisitos previos](#requisitos-previos)
- [Backend](#backend)
- [Pruebas](#pruebas)
- [Frontend](#frontend)
- [Ejecutar todo junto](#ejecutar-todo-junto)
- [Casos de prueba manuales](#casos-de-prueba-manuales)
- [Solución de problemas](#solución-de-problemas)
- [Alcance, limitaciones y próximos pasos](#alcance-limitaciones-y-próximos-pasos)
- [Referencias](#referencias)

---

## ¿Cómo funciona?

1. El usuario elige **origen**, **destino** y, si quiere, **paradas** en la interfaz (React).
2. React envía esa solicitud al backend (`POST /api/routes/shortest-path`).
3. El backend ejecuta **Dijkstra** sobre el grafo, una vez por cada tramo (origen → parada 1 → … → destino).
4. El backend responde con la secuencia de nodos, duración, distancia, geometría vial y métricas de las ejecuciones de Dijkstra.
5. React muestra el resultado, los tramos calculados y las aristas examinadas; Leaflet dibuja la ruta siguiendo las calles.

### Glosario rápido

| Término                 | Significado en este proyecto                                                                                           |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Nodo / vértice**      | Una ubicación (p. ej. `A` = Universidad EAN).                                                                          |
| **Arista**              | Una conexión de un nodo a otro, con distancia (m) y duración (s).                                                      |
| **Grafo dirigido**      | Cada arista tiene sentido: `A→C` y `C→A` son aristas distintas, con pesos distintos.                                   |
| **Peso**                | El costo de una arista. Dijkstra minimiza `duration_seconds`.                                                          |
| **Lista de adyacencia** | Para cada nodo se guarda solo la lista de sus vecinos de salida.                                                       |
| **Dijkstra**            | Algoritmo que encuentra el camino de menor costo entre dos nodos.                                                      |
| **Heap**                | Cola de prioridad (`heapq`) que entrega siempre el nodo pendiente más barato.                                          |
| **OSRM**                | Servicio de enrutamiento consultado al generar las aristas para obtener distancia, duración estimada y geometría vial. |
| **CORS**                | Permiso que el backend da al navegador para que el frontend lo llame desde otro puerto.                                |

---

## Estado del proyecto

| Parte                                       | Estado                                                                                   |
| ------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Modelo del grafo, carga de datos y Dijkstra | Implementado y probado                                                                   |
| API (FastAPI)                               | Implementada y probada                                                                   |
| Pruebas automatizadas (pytest)              | **43 pruebas, todas pasan** (verificado en macOS con Python 3.14)                        |
| Grafo de datos                              | 16 nodos y 68 aristas dirigidas, con valores de OSRM                                     |
| Frontend (React + Leaflet + Tailwind)       | Implementado; se levanta con `npm run dev`                                               |
| Ruta dibujada siguiendo las calles          | Implementada mediante la geometría vial almacenada en las aristas y mostrada con Leaflet |

## Arquitectura

```
┌────────────────────┐   HTTP/JSON    ┌────────────────────────────┐
│ Frontend           │ ─────────────► │ Backend (FastAPI)          │
│ React + TypeScript │                │  routes → graph_service    │
│ Leaflet / OSM      │ ◄───────────── │         → dijkstra → models│
└────────────────────┘                └────────────────────────────┘
        solo visualiza                    calcula la ruta mínima
```

| Capa      | Tecnología                                                                  |
| --------- | --------------------------------------------------------------------------- |
| Backend   | Python 3.11+, FastAPI, Uvicorn, Pydantic v2                                 |
| Algoritmo | Python estándar (`heapq`), sin librerías de grafos                          |
| Pruebas   | pytest y httpx                                                              |
| Frontend  | React, TypeScript, Vite                                                     |
| Estilos   | Tailwind CSS v4 con archivos `*.module.css`                                 |
| Mapa      | Leaflet + react-leaflet + OpenStreetMap (sin API key)                       |
| Datos     | JSON en memoria (sin base de datos); distancias y tiempos obtenidos de OSRM |

## Estructura de carpetas

```
logiexpress/
├── README.md
├── NOTAS_SUSTENTACION.md          # guion y respuestas para la sustentación
├── backend/
│   ├── pytest.ini                 # configuración de pytest (va en backend/, NO en tests/)
│   ├── requirements.txt
│   ├── generate_edges.py          # script auxiliar: consulta OSRM y genera las aristas
│   ├── verify_graph.py            # comprueba el JSON generado (aristas, duplicados, geometría, conexidad)
│   ├── data/
│   │   ├── sample_graph.json      # grafo usado por la app: 16 nodos + 68 aristas
│   │   └── edges_generated.json   # salida cruda de generate_edges.py (registro)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models.py              # Node, Edge, Graph y errores de dominio
│   │   ├── graph_service.py       # carga el JSON y construye el Graph
│   │   ├── dijkstra.py            # algoritmo y reconstrucción del camino
│   │   ├── schemas.py             # contratos Pydantic de la API
│   │   ├── routes.py              # endpoints HTTP
│   │   └── main.py                # aplicación FastAPI y CORS
│   └── tests/
│       ├── __init__.py            # vacío: convierte la carpeta en paquete
│       ├── helpers.py             # grafo pequeño compartido (no es un test)
│       ├── test_graph.py          # 21 pruebas del modelo y la carga de datos
│       ├── test_dijkstra.py       # 13 pruebas del algoritmo
│       └── test_api.py            # 9 pruebas de los endpoints
└── frontend/
    ├── .env.example
    ├── vite.config.ts
    └── src/
        ├── main.tsx
        ├── App.tsx / App.module.css
        ├── index.css              # único @import "tailwindcss"
        ├── types/route.ts         # tipos alineados con schemas.py
        ├── services/routingService.ts
        └── components/
            ├── LocationSelector.tsx / .module.css
            ├── RouteResult.tsx      / .module.css
            └── MapView.tsx          / .module.css
```

## Los datos: ubicaciones y conexiones

### Las 16 ubicaciones

| ID  | Ubicación                     | ID  | Ubicación                               |
| --- | ----------------------------- | --- | --------------------------------------- |
| A   | Universidad EAN               | I   | Plaza de Mercado Paloquemao             |
| B   | Plaza de Bolívar              | J   | Torre Colpatria                         |
| C   | Movistar Arena                | K   | Edificio Atrio Bancolombia              |
| D   | Centro Comercial Multiplaza   | L   | Centro Comercial Hacienda Santa Bárbara |
| E   | Aeropuerto El Dorado          | M   | Club Campestre Guaymaral                |
| F   | Clínica Los Cobos             | N   | Mundo Aventura                          |
| G   | Centro Comercial Centro Mayor | O   | Monserrate                              |
| H   | Alto de Patios                | P   | Vive Claro Distrito Cultural            |

Algunas coordenadas son aproximadas (un punto de referencia del lugar). El ID es estable: **no lo cambies** sin actualizar todas las aristas.

### Las 68 aristas dirigidas

- Se definieron **34 pares de conexiones candidatas** (lista `CONNECTIONS` en `generate_edges.py`). No se conectan todos con todos.
- Para cada par se consulta OSRM en **ambos sentidos**, lo que genera 68 aristas dirigidas. La ida y la vuelta pueden diferir en distancia, duración y geometría.
- Cada arista almacena `distance_meters`, `duration_seconds` y `geometry` (coordenadas de la ruta vial).
- Los tiempos son **estimaciones del perfil de conducción de OSRM**, no mediciones de tráfico en vivo.
- El grafo resultante es **fuertemente conexo**: existe un camino dirigido entre cualquier par de nodos.

---

## Requisitos previos

| Herramienta           | Versión                              | Para qué                                            |
| --------------------- | ------------------------------------ | --------------------------------------------------- |
| Python                | 3.11 o superior (probado con 3.14)   | Backend y pruebas                                   |
| Node.js (incluye npm) | 20 o superior (se recomienda la LTS) | Frontend                                            |
| Conexión a internet   | —                                    | Teselas del mapa y, solo si regeneras aristas, OSRM |

### Instalar las herramientas

**macOS** (con [Homebrew](https://brew.sh)):

```bash
brew install python node
python3 --version     # debe mostrar 3.11 o superior
node --version
```

**Windows** (PowerShell):

```powershell
winget install Python.Python.3.12
winget install OpenJS.NodeJS.LTS
# Cierra y vuelve a abrir PowerShell para que reconozca los comandos nuevos
py --version
node --version
```

> Alternativa en Windows: descarga el instalador de [python.org](https://www.python.org/downloads/) y marca la casilla **"Add python.exe to PATH"** durante la instalación. Node.js se descarga de [nodejs.org](https://nodejs.org).

---

## Backend

Todos los comandos se ejecutan desde la carpeta `backend/`.

### Instalación (una sola vez)

Se usa un **entorno virtual** para no mezclar las librerías del proyecto con las del sistema. Con el Python de Homebrew, instalar fuera de uno falla con el error `externally-managed-environment`.

**macOS:**

```bash
cd backend
python3 -m venv venv              # crea la carpeta venv/
source venv/bin/activate          # activa el entorno: el prompt muestra (venv)
pip install -r requirements.txt   # instala FastAPI, Uvicorn, Pydantic, pytest, httpx
```

**Windows (PowerShell):**

```powershell
cd backend
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Windows (CMD):**

```bat
cd backend
py -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

> Si PowerShell dice que la ejecución de scripts está deshabilitada, ejecuta una vez
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` y vuelve a activar el entorno.

Para salir del entorno virtual, en cualquier sistema: `deactivate`.

### Ejecución

Con el entorno activo (debe verse `(venv)` en la terminal):

```bash
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

- `--reload` reinicia el servidor solo cuando cambias el código.
- API: `http://localhost:8000`
- Documentación interactiva (Swagger): `http://localhost:8000/docs`

Al arrancar, el servidor carga `data/sample_graph.json`. Si el archivo es inválido, falla de inmediato con un mensaje claro.

**Comprobar que responde:**

```bash
# macOS (o Windows con curl.exe)
curl http://localhost:8000/api/health
# Respuesta esperada: {"status":"ok"}
```

```powershell
# Windows PowerShell
Invoke-RestMethod http://localhost:8000/api/health
```

### Cómo está modelado el grafo

El grafo es **dirigido** y usa una **lista de adyacencia** basada en diccionarios. El archivo JSON almacena nodos y aristas; al cargarlo, `Graph` construye en memoria una estructura de vecinos de salida para cada nodo:

```python
_adjacency = {
    "A": {"C": Edge(A→C, 3839 m, 542 s), "J": Edge(A→J, ...), "L": Edge(A→L, ...), "O": Edge(A→O, 9221 m, 878 s)},
    "C": {"A": Edge(C→A, 5118 m, 489 s), "P": Edge(C→P, ...), "I": Edge(C→I, ...), "N": Edge(C→N, ...), "O": Edge(C→O, ...)},
    # ...
}
```

- Una calle de **doble sentido** se representa con dos aristas (`A→C` y `C→A`); una de **sentido único**, con una sola.
- Cada arista guarda `distance_meters`, `duration_seconds` y `geometry`. **Dijkstra minimiza la duración** y suma la distancia de las mismas aristas seleccionadas como métrica adicional.
- Los pesos deben ser números finitos y mayores o iguales a cero; si no, `Edge` lanza `InvalidWeightError`. Esto garantiza la condición que necesita Dijkstra.
- Espacio O(V + E) y vecinos de un nodo en O(grado de salida), adecuado para redes viales dispersas (una matriz de adyacencia usaría O(V²)).

### Algoritmo

`shortest_path(graph, origin, destination)` en `dijkstra.py`:

- Usa `heapq` como cola de prioridad, diccionarios de distancias y predecesores, y un conjunto de visitados.
- Descarta entradas obsoletas del heap y se detiene al extraer el destino.
- Complejidad **O((V + E) log V)**.
- Casos controlados: origen igual a destino (camino de un nodo, costo 0), nodo inexistente (`NodeNotFoundError`) y destino inalcanzable (`NoPathError`).

**Puntos intermedios:** el endpoint ejecuta Dijkstra por cada tramo consecutivo (origen → parada 1 → … → destino) y concatena los caminos sin repetir el nodo de unión. El **orden de las paradas es el que indica el usuario**; no se optimiza.

> El detalle paso a paso (con un ejemplo real A → B) está en `NOTAS_SUSTENTACION.md`.

### Formato del grafo (`data/sample_graph.json`)

Una **única fuente de datos**: nodos y aristas en el mismo archivo.

```json
{
  "nodes": [
    { "id": "A", "name": "Universidad EAN", "lat": 4.663667, "lng": -74.056726 }
  ],
  "edges": [
    {
      "origin": "A",
      "destination": "C",
      "distance_meters": 3839,
      "duration_seconds": 542
    }
  ]
}
```

### Endpoints

| Método y ruta                    | Descripción                         | Códigos            |
| -------------------------------- | ----------------------------------- | ------------------ |
| `GET /api/health`                | Verifica que el backend está activo | 200                |
| `GET /api/graph`                 | Nodos y aristas del grafo           | 200                |
| `GET /api/locations`             | Ubicaciones con coordenadas         | 200                |
| `POST /api/routes/shortest-path` | Calcula la ruta mínima              | 200, 400, 404, 422 |

**Solicitud** (`stops` es opcional). Ejemplo: de A a G pasando por E.

```bash
# macOS
curl -X POST http://localhost:8000/api/routes/shortest-path \
  -H "Content-Type: application/json" \
  -d '{"origin":"A","destination":"G","stops":["E"]}'
```

```powershell
# Windows PowerShell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/routes/shortest-path `
  -ContentType "application/json" `
  -Body '{"origin":"A","destination":"G","stops":["E"]}'
```

**Respuesta** (abreviada; valores reales con el grafo de 68 aristas):

```json
{
  "algorithm": "Dijkstra",
  "path": ["A", "C", "P", "E", "D", "G"],
  "total_duration_seconds": 3570.0,
  "total_distance_meters": 36525.0,
  "nodes": [
    { "id": "A", "name": "Universidad EAN", "lat": 4.663667, "lng": -74.056726 }
  ],
  "geometry": [[4.66372, -74.05681], [4.66326, -74.0571], ...],
  "segments": [
    {"origin": "A", "destination": "E", "node_count": 4, "examined_edges": 56},
    {"origin": "E", "destination": "G", "node_count": 3, "examined_edges": 22}
  ],
  "total_examined_edges": 78
}
```

`geometry` trae el trazado por calles de todo el camino (en este ejemplo, más de 1300 puntos). Con una parada hay **dos tramos**: `A → E` y `E → G`.

`nodes` sigue el orden de `path` y puede repetir ids si una parada obliga a pasar dos veces por el mismo nodo. `segments` informa cada tramo calculado de forma independiente; `node_count` cuenta los nodos de ese tramo y `examined_edges` las aristas inspeccionadas durante esa ejecución. `total_examined_edges` suma los contadores de todos los tramos. Las aristas examinadas no son las que forman el camino final: se cuentan **todas las aristas de salida inspeccionadas** de los nodos que se procesan, incluidas las que llevan a un vecino ya visitado y se descartan. En el ejemplo, 56 + 22 = 78.

**Errores:**

| Código | Causa                           | Ejemplo de `detail`                  |
| ------ | ------------------------------- | ------------------------------------ |
| 400    | Un nodo enviado no existe       | `El nodo 'Z' no existe en el grafo.` |
| 404    | No hay camino entre dos puntos  | `No existe ruta de 'A' a 'D'.`       |
| 422    | Cuerpo de la solicitud inválido | Validación de Pydantic               |

> Con el grafo actual no se puede provocar un 404 (es conexo). Ese caso se comprueba en las pruebas automatizadas con un grafo pequeño que sí tiene un nodo aislado.

### CORS

El navegador bloquea que el frontend (puerto de Vite) llame al backend (puerto 8000) salvo que el backend lo autorice. `main.py` permite `http://localhost:5173` a `5180` y `http://127.0.0.1:5173`. Vite usa el 5173 y, si está ocupado, prueba el siguiente. Si tu frontend corre en otro puerto, agrégalo a `FRONTEND_ORIGINS` en `backend/app/main.py`.

### Regenerar las aristas (opcional)

Solo hace falta si cambias las ubicaciones o la lista de conexiones. **No es necesario para usar la aplicación.**

```bash
cd backend
# con el entorno virtual activo y conexión a internet
python generate_edges.py        # en Windows también puede ser: py generate_edges.py
```

- Lee las ubicaciones de `data/sample_graph.json` y las conexiones de la lista `CONNECTIONS` dentro del script.
- Consulta el servidor público de OSRM en ambos sentidos para cada par candidato y obtiene distancia, duración estimada y geometría vial.
- Genera o actualiza `data/sample_graph.json`, conserva una copia de respaldo y produce `data/edges_generated.json` como salida del proceso.
- Si una conexión no tiene ruta, el script lo avisa con `Sin ruta: X -> Y` y no la incluye.
- Es un servicio público de demostración: úsalo con moderación.
- Después de regenerar, **reinicia uvicorn** (`get_graph()` usa `lru_cache` y solo lee el JSON al arrancar) y verifica el resultado:

```bash
python verify_graph.py
```

`verify_graph.py` comprueba 16 nodos, 68 aristas dirigidas (34 conexiones), sin duplicados, cada conexión en ambos sentidos, pesos positivos, `geometry` con al menos 2 puntos y grafo fuertemente conexo. Si cambias el número de conexiones, actualiza `N_CONEXIONES` y `N_ARISTAS` dentro del script.

---

## Pruebas

Las pruebas verifican el modelo del grafo, Dijkstra y los endpoints **sin necesidad de abrir el navegador ni el mapa**.

### Dónde va cada archivo

```
backend/
├── pytest.ini        ← configuración: aquí, junto a requirements.txt
└── tests/
    ├── __init__.py   ← vacío
    ├── helpers.py    ← grafo pequeño que usan los demás
    ├── test_graph.py
    ├── test_dijkstra.py
    └── test_api.py
```

`pytest.ini` contiene `pythonpath = .`, que permite a los tests hacer `from app.models import ...`. Por eso las pruebas **siempre se ejecutan desde `backend/`**.

### Ejecutarlas

Con el entorno virtual activo:

**macOS:**

```bash
cd backend
source venv/bin/activate
pytest -v
```

**Windows (PowerShell):**

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pytest -v
```

Resultado esperado al final:

```
============ 43 passed, 1 warning in 0.3s ============
```

La advertencia sobre `httpx` (`StarletteDeprecationWarning`) es un aviso de las librerías y no afecta a los resultados.

Variantes útiles:

```bash
pytest -v tests/test_dijkstra.py          # solo un archivo
pytest -v -k "asimetricas"                # solo las pruebas cuyo nombre contenga ese texto
pytest -x                                 # se detiene en el primer fallo
```

### Qué prueba cada archivo

| Archivo            | Pruebas | Qué cubre                                                                                                                                                                                                                                                                                       |
| ------------------ | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_graph.py`    | 21      | Nodos duplicados o inexistentes; pesos negativos o no finitos; arista a sí mismo; grafo dirigido y aristas asimétricas; errores al cargar el JSON (archivo faltante, JSON roto, campo faltante, peso escrito como texto); datos reales (16 nodos, 68 aristas, pesos positivos, sentido inverso) |
| `test_dijkstra.py` | 13      | Ruta directa y alternativa; minimiza duración y no distancia; origen igual a destino; destino inalcanzable; nodo inexistente; aristas asimétricas; comparación con fuerza bruta; y, con el grafo real, los 240 pares origen-destino y la condición de optimalidad                               |
| `test_api.py`      | 9       | Endpoints de consulta; ruta simple; ruta con parada intermedia (suma de tramos); errores 400, 404 y 422                                                                                                                                                                                         |

### Por qué hay un grafo pequeño aparte

`tests/helpers.py` define un grafo de 5 nodos con resultados calculados a mano (incluye un nodo aislado y otro que solo tiene salidas). Así las pruebas siguen valiendo aunque cambien los pesos de `sample_graph.json`, y permiten probar el caso "sin ruta", imposible con el grafo real.

---

## Frontend

### Instalación

**En la carpeta `frontend/` del proyecto:** entra y ejecuta `npm install`.

```


### Configuración

`.env` contiene la URL del backend y debido a que el proyecto al clonarse viene sin el .env, debe crearse el fichero:

```

VITE_API_URL=http://localhost:8000

````

No se necesita ninguna clave de API: el mapa usa teselas públicas de OpenStreetMap.

### Ejecución

```bash
cd frontend
npm run dev
````

La terminal muestra la dirección, normalmente `http://localhost:5173`. Si muestra otro puerto, comprueba que esté en `FRONTEND_ORIGINS` (ver [CORS](#cors)).

### Componentes

| Archivo                      | Función                                                                                                                                            |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `types/route.ts`             | Tipos `NodeOut`, `EdgeOut`, `GraphResponse`, `RouteRequest`, `RouteSegment` y `RouteResponse`, alineados con `schemas.py` (campos en `snake_case`) |
| `services/routingService.ts` | `getLocations`, `getGraph`, `calculateRoute`. Convierte los errores 400, 404, 422 y el backend apagado en mensajes legibles (`ApiError`)           |
| `LocationSelector.tsx`       | Origen, destino y paradas que se pueden agregar, quitar y reordenar con ↑ y ↓. No envía paradas sin elegir                                         |
| `RouteResult.tsx`            | Duración, distancia, secuencia de nodos, cantidad de tramos, aristas examinadas y detalle de cada tramo                                            |
| `MapView.tsx`                | Mapa Leaflet: ubicaciones y geometría vial de la ruta; origen en verde y destino en rojo                                                           |
| `App.tsx`                    | Estado local y composición de los componentes                                                                                                      |

### Estilos: Tailwind con CSS Modules

Cada componente tiene su propio archivo `*.module.css` con clases definidas mediante `@apply`:

```css
@reference "../index.css";

.primaryButton {
  @apply rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white;
}
```

El componente las usa como `styles.primaryButton`. `index.css` contiene el único `@import "tailwindcss"` y la línea `@reference` es obligatoria en cada módulo (Tailwind v4).

Los colores de los marcadores del mapa están definidos como constantes dentro de `MapView.tsx`, porque Leaflet los recibe como opciones y no como clases CSS.

---

## Ejecutar todo junto

Se necesita levantar **dos terminales a la vez**: una para el backend y otra para el frontend.

**Terminal 1: backend**

```bash
# macOS
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

```powershell
# Windows PowerShell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**Terminal 2: frontend** (igual en macOS y Windows)

```bash
cd frontend
npm run dev
```

Abre `http://localhost:5173`. Para detener cualquiera de los dos servidores: `Ctrl + C`.

## Casos de prueba manuales

Resultados con el grafo actual (16 nodos, 68 aristas). Puedes comprobarlos en la interfaz o en Swagger (`/docs`). La última columna es `total_examined_edges` (aristas de salida inspeccionadas, sumadas por tramo).

| Consulta                           | Camino mínimo       | Duración | Distancia | Aristas examinadas |
| ---------------------------------- | ------------------- | -------- | --------- | ------------------ |
| A → B                              | A, J, B             | 1103 s   | 9078 m    | 41                 |
| A → E                              | A, C, P, E          | 1812 s   | 16431 m   | 56                 |
| A → M                              | A, L, M             | 1831 s   | 23451 m   | 59                 |
| B → M                              | B, J, A, L, M       | 2998 s   | 36423 m   | 64                 |
| G → F                              | G, I, C, A, L, F    | 2248 s   | 23868 m   | 55                 |
| N → H                              | N, G, I, K, H       | 3247 s   | 30401 m   | 63                 |
| K → O                              | K, O                | 235 s    | 2323 m    | 8                  |
| A → G con parada E                 | A, C, P, E, D, G    | 3570 s   | 36525 m   | 78 (56 + 22)       |
| M → G con parada O                 | M, L, A, O, K, I, G | 4362 s   | 46385 m   | 83 (48 + 35)       |
| A → N con parada P                 | A, C, P, C, N       | 2450 s   | 22286 m   | 83 (31 + 52)       |
| A → C                              | A, C                | 542 s    | 3839 m    | 9                  |
| C → A (asimetría respecto a A → C) | C, A                | 489 s    | 5118 m    | 10                 |
| A → A                              | A                   | 0 s      | 0 m       | 0                  |
| A → Z (nodo inexistente)           | Error 400           | —        | —         | —                  |

Observación útil para la demostración: **A → B no tiene arista directa**, por lo que Dijkstra elige el rodeo por J. Los tiempos de A → C y C → A difieren porque el grafo es dirigido.

**Dos comprobaciones recomendadas:** _A → G con parada E_ (dos tramos; C, P y D son nodos de paso, no paradas) y _M → G con parada O_ (sin la parada la ruta sería M, N, G en 3073 s; forzar O la alarga a 4362 s). **A → N con parada P retrocede por C**: tras llegar a P, ir a N por C cuesta 473 + 1058 = 1531 s y por D, 853 + 752 = 1605 s. Es el comportamiento correcto de Dijkstra por tramos, pero conviene explicarlo.

## Solución de problemas

| Síntoma                                                       | Causa probable y solución                                                                                                                                                                                    |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `externally-managed-environment` al instalar con pip          | Activa un entorno virtual (`python3 -m venv venv`)                                                                                                                                                           |
| `source: no such file or directory: .venv/bin/activate`       | La carpeta se llama `venv`, no `.venv`: usa `source venv/bin/activate`                                                                                                                                       |
| `python3` o `py` no se reconoce (Windows)                     | Reinstala Python marcando "Add python.exe to PATH", o reabre la terminal tras instalarlo                                                                                                                     |
| PowerShell: "la ejecución de scripts está deshabilitada"      | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` y activa de nuevo el entorno                                                                                                          |
| `zsh: no matches found: uvicorn[standard]`                    | Escribe `"uvicorn[standard]"` entre comillas, o usa `requirements.txt`                                                                                                                                       |
| `ModuleNotFoundError: No module named 'app'` al correr pytest | Ejecútalo desde `backend/` (donde está `pytest.ini`), no desde `tests/` ni desde la raíz                                                                                                                     |
| `uvicorn` no se reconoce                                      | El entorno virtual no está activo (debe verse `(venv)` en la terminal)                                                                                                                                       |
| El puerto 8000 ya está en uso                                 | macOS: `lsof -i :8000`; Windows: `netstat -ano \| findstr :8000`. Con `--reload` uvicorn crea **dos procesos**: cierra ambos (`kill -9 PID1 PID2` en macOS) o usa `--port 8001` (y actualiza `VITE_API_URL`) |
| La interfaz dice "No se pudo conectar con el backend"         | El backend no está corriendo, o `VITE_API_URL` apunta a otro puerto                                                                                                                                          |
| Error de CORS en la consola del navegador                     | El puerto del frontend no está en `FRONTEND_ORIGINS` de `main.py`                                                                                                                                            |
| Error de dependencias con `react-leaflet`                     | La v5 exige React 19. Con React 18 usa `npm install react-leaflet@4`                                                                                                                                         |
| Los estilos no se aplican o falla `@reference`                | Revisa que `vite.config.ts` incluya el plugin `@tailwindcss/vite` y que Tailwind sea v4                                                                                                                      |
| El mapa aparece gris o sin teselas                            | Revisa la conexión a internet: las teselas se descargan de OpenStreetMap                                                                                                                                     |
| El servidor falla al arrancar con "Datos de grafo inválidos"  | Revisa `data/sample_graph.json`: ids duplicados, aristas a nodos inexistentes, pesos negativos o números escritos como texto                                                                                 |
| `generate_edges.py` falla con error de ruta o archivo         | Ejecútalo desde `backend/`: usa rutas relativas (`data/...`)                                                                                                                                                 |

## Alcance, limitaciones y próximos pasos

**Incluido:** modelo de grafo dirigido, Dijkstra propio, paradas intermedias en el orden indicado, API REST, pruebas automatizadas, interfaz web y mapa.

**Fuera de alcance:**

- Base de datos, autenticación, Docker, caché o microservicios.
- Tráfico en tiempo real.
- Floyd-Warshall como parte de la aplicación (el notebook complementario lo usa solo como verificación independiente de Dijkstra).
- Optimización del orden de las paradas (problema del viajante, TSP).

**Limitaciones conocidas:**

- El grafo es una **abstracción simplificada** de Bogotá con 16 ubicaciones y 68 aristas dirigidas; no representa todas las calles ni todas las conexiones posibles.
- Dijkstra garantiza el camino de menor duración **dentro del grafo modelado**, no la ruta óptima de toda Bogotá.
- Los tiempos son estimaciones del perfil de conducción de OSRM; no representan tráfico en vivo.
- Las coordenadas de algunos puntos de referencia pueden ser aproximadas.
- El orden de las paradas intermedias es el que indica el usuario. El sistema no optimiza el orden de visita ni resuelve el problema del viajante (TSP).
- El servidor público de teselas de OpenStreetMap y el de OSRM son para uso moderado; mantén visible la atribución del mapa.

**Geometría vial:** ya está implementada. Las aristas contienen la geometría obtenida de OSRM; el backend concatena las geometrías de las aristas elegidas por Dijkstra y el frontend las representa con Leaflet.

**Métricas de búsqueda:** la respuesta incluye el número de tramos calculados y las aristas examinadas por cada ejecución de Dijkstra, además del total acumulado. Las aristas examinadas representan conexiones inspeccionadas durante la búsqueda, no solamente las aristas del camino final.

## Notebook complementario

`LogiExpress_Notebook.ipynb` es una entrega autocontenida: reúne el modelo del grafo, Dijkstra, la verificación contra Floyd-Warshall en los 240 pares, dos comprobaciones con mapa (A → G con parada E y M → G con parada O), los casos de demostración y los casos de error. No necesita FastAPI ni React. Si `sample_graph.json` está junto al notebook (o en `backend/data/`), lo usa con la geometría completa; si no, usa una copia embebida de los mismos datos con el trazado por calles simplificado de las rutas de demostración. Requiere `matplotlib`.

## Referencias

- FastAPI: https://fastapi.tiangolo.com/
- Pydantic: https://docs.pydantic.dev/
- pytest: https://docs.pytest.org/
- OSRM (servicio de rutas): https://project-osrm.org/
- React: https://react.dev/ · Vite: https://vite.dev/guide/
- Tailwind CSS: https://tailwindcss.com/docs
- Leaflet: https://leafletjs.com/ · React Leaflet: https://react-leaflet.js.org/
- Política de teselas de OpenStreetMap: https://operations.osmfoundation.org/policies/tiles/
- Python `heapq`: https://docs.python.org/3/library/heapq.html

Revisar las versiones vigentes de las dependencias al momento de instalar.
