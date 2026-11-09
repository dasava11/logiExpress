/**
 * Mapa Leaflet + OpenStreetMap. Solo VISUALIZA: dibuja las ubicaciones y la
 * ruta que ya calculó el backend; no calcula nada.
 */
import { useEffect, useMemo } from "react";
import {
  CircleMarker,
  MapContainer,
  Polyline,
  Popup,
  TileLayer,
  useMap,
} from "react-leaflet";
import type { LatLngTuple } from "leaflet";
import "leaflet/dist/leaflet.css";
import type { NodeOut, RouteResponse } from "../types/route";
import styles from "./MapView.module.css";

interface Props {
  locations: NodeOut[];
  route: RouteResponse | null;
}

const DEFAULT_CENTER: LatLngTuple = [4.625, -74.08];

// Los marcadores de Leaflet son SVG y reciben colores por opciones, no por clases CSS.
const COLORS = {
  idle: "#94a3b8", // gris: ubicación fuera de la ruta
  via: "#2563eb", // azul: en la ruta
  start: "#16a34a", // verde: origen
  end: "#dc2626", // rojo: destino
};

/** Ajusta el encuadre del mapa a los puntos dados cada vez que cambian. */
function FitBounds({ points }: { points: LatLngTuple[] }) {
  const map = useMap();
  useEffect(() => {
    if (points.length > 0) map.fitBounds(points, { padding: [40, 40] });
  }, [map, points]);
  return null;
}

export default function MapView({ locations, route }: Props) {
  const linePoints = useMemo<LatLngTuple[]>(
    () =>
      route && route.geometry.length > 1
        ? route.geometry
        : route
          ? route.nodes.map((n): LatLngTuple => [n.lat, n.lng])
          : [],
    [route],
  );

  const fitPoints = useMemo<LatLngTuple[]>(
    () =>
      linePoints.length > 0
        ? linePoints
        : locations.map((l): LatLngTuple => [l.lat, l.lng]),
    [linePoints, locations],
  );

  const startId = route?.path[0];
  const endId = route?.path[route.path.length - 1];
  const routeIds = new Set(route?.path ?? []);

  const colorFor = (id: string): string => {
    if (id === startId) return COLORS.start;
    if (id === endId) return COLORS.end;
    return routeIds.has(id) ? COLORS.via : COLORS.idle;
  };

  return (
    <div className={styles.wrapper}>
      <MapContainer center={DEFAULT_CENTER} zoom={12} className={styles.map}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitBounds points={fitPoints} />

        {linePoints.length > 1 && (
        <Polyline positions={linePoints} pathOptions={{ color: COLORS.via, weight: 5 }} />
        )}

        {locations.map((location) => (
          <CircleMarker
            key={location.id}
            center={[location.lat, location.lng]}
            radius={routeIds.has(location.id) ? 10 : 7}
            pathOptions={{
              color: "#ffffff",
              weight: 2,
              fillColor: colorFor(location.id),
              fillOpacity: 1,
            }}
          >
            <Popup>
              <strong>{location.id}</strong> · {location.name}
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>

      <p className={styles.note}>
        Trazado por calles según OSRM.
      </p>
    </div>
  );
}
