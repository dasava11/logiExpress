/**
 * Objetos tipados que representan las respuestas de la API. Reflejan exactamente backend/app/schemas.py
 * (mismos nombres de modelos y de campos, incluido snake_case).
 */

export interface NodeOut {
  id: string;
  name: string;
  lat: number;
  lng: number;
}

export interface EdgeOut {
  origin: string;
  destination: string;
  distance_meters: number;
  duration_seconds: number;
}

export interface GraphResponse {
  nodes: NodeOut[];
  edges: EdgeOut[];
}

export interface RouteRequest {
  origin: string;
  destination: string;
  /** Paradas intermedias en el orden de visita. */
  stops: string[];
}

export interface RouteSegment {
  origin: string;
  destination: string;
  node_count: number;
  examined_edges: number;
}

export interface RouteResponse {
  algorithm: string;
  path: string[];
  total_duration_seconds: number;
  total_distance_meters: number;
  /** Nodos de `path` en el mismo orden; un id puede repetirse. */
  nodes: NodeOut[];
  geometry: [number, number][];
  /** Resultado individual de cada tramo calculado con Dijkstra. */
  segments: RouteSegment[];
  /** Suma de las aristas examinadas en todos los tramos. */
  total_examined_edges: number;
}
