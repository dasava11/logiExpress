/** Cliente HTTP del backend. Todo acceso a la API pasa por este archivo. */
import type {
  GraphResponse,
  NodeOut,
  RouteRequest,
  RouteResponse,
} from "../types/route";

const API_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

/** Error de la API con el código HTTP (0 si el backend no respondió). */
export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** Extrae el mensaje `detail` de FastAPI (string en 400/404, lista en 422). */
async function readErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) return "La solicitud no es válida.";
  } catch {
    // El cuerpo no era JSON: se usa el mensaje genérico.
  }
  return `Error ${response.status} del servidor.`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, init);
  } catch {
    throw new ApiError(
      `No se pudo conectar con el backend en ${API_URL}. ¿Está en ejecución?`,
      0,
    );
  }
  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response), response.status);
  }
  return (await response.json()) as T;
}

export function getLocations(): Promise<NodeOut[]> {
  return request<NodeOut[]>("/api/locations");
}

export function getGraph(): Promise<GraphResponse> {
  return request<GraphResponse>("/api/graph");
}

export function calculateRoute(body: RouteRequest): Promise<RouteResponse> {
  return request<RouteResponse>("/api/routes/shortest-path", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
