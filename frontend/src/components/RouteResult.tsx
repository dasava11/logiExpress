/** Panel con el resultado calculado por el backend (o el error devuelto). */
import type { RouteResponse } from "../types/route";
import styles from "./RouteResult.module.css";

interface Props {
  route: RouteResponse | null;
  error: string | null;
}

function formatDuration(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.round(totalSeconds % 60);
  if (minutes === 0) return `${seconds} s`;
  return seconds === 0 ? `${minutes} min` : `${minutes} min ${seconds} s`;
}

function formatDistance(meters: number): string {
  return meters < 1000 ? `${Math.round(meters)} m` : `${(meters / 1000).toFixed(1)} km`;
}

export default function RouteResult({ route, error }: Props) {
  if (error) {
    return (
      <div role="alert" className={styles.error}>
        {error}
      </div>
    );
  }

  if (!route) {
    return <p className={styles.placeholder}>Elige origen y destino para calcular una ruta.</p>;
  }

  return (
    <section className={styles.card}>
      <h2 className={styles.title}>Ruta calculada ({route.algorithm})</h2>

      <dl className={styles.metrics}>
        <div>
          <dt className={styles.metricLabel}>Duración</dt>
          <dd className={styles.metricValue}>{formatDuration(route.total_duration_seconds)}</dd>
        </div>
        <div>
          <dt className={styles.metricLabel}>Distancia</dt>
          <dd className={styles.metricValue}>{formatDistance(route.total_distance_meters)}</dd>
        </div>
      </dl>

      <h3 className={styles.subtitle}>Secuencia</h3>
      <ol className={styles.sequence}>
        {route.nodes.map((node, index) => (
          <li key={`${node.id}-${index}`} className={styles.step}>
            <span className={styles.badge}>{node.id}</span>
            <span>{node.name}</span>
          </li>
        ))}
      </ol>

       <h3 className={styles.subtitle}>Análisis de Dijkstra</h3>

      <dl className={styles.algorithmMetrics}>
        <div>
          <dt className={styles.metricLabel}>Tramos calculados</dt>
          <dd className={styles.metricValue}>
            {route.segments.length}
          </dd>
        </div>

        <div>
          <dt className={styles.metricLabel}>Aristas examinadas</dt>
          <dd className={styles.metricValue}>
            {route.total_examined_edges}
          </dd>
        </div>
      </dl>

      <div className={styles.segments}>
        {route.segments.map((segment, index) => (
          <div
            key={`${segment.origin}-${segment.destination}-${index}`}
            className={styles.segment}
          >
            <span>
              Tramo {index + 1}: {segment.origin} → {segment.destination}
            </span>

            <span className={styles.segmentDetail}>
              {segment.node_count} nodos
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
