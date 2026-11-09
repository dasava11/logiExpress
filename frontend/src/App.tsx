/** Composición de la interfaz: estado local con React básico, sin librerías extra. */
import { useEffect, useState } from "react";
import LocationSelector from "./components/LocationSelector";
import MapView from "./components/MapView";
import RouteResult from "./components/RouteResult";
import { ApiError, calculateRoute, getLocations } from "./services/routingService";
import type { NodeOut, RouteResponse } from "./types/route";
import styles from "./App.module.css";

export default function App() {
  const [locations, setLocations] = useState<NodeOut[]>([]);
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [stops, setStops] = useState<string[]>([]);
  const [route, setRoute] = useState<RouteResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getLocations()
      .then(setLocations)
      .catch((e: unknown) => setError(describeError(e)));
  }, []);

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await calculateRoute({
        origin,
        destination,
        stops: stops.filter((s) => s !== ""),
      });
      setRoute(result);
    } catch (e) {
      setRoute(null);
      setError(describeError(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <h1 className={styles.title}>LogiExpress</h1>
        <LocationSelector
          locations={locations}
          origin={origin}
          destination={destination}
          stops={stops}
          disabled={loading}
          onOriginChange={setOrigin}
          onDestinationChange={setDestination}
          onStopsChange={setStops}
          onSubmit={handleSubmit}
        />
        <RouteResult route={route} error={error} />
      </aside>
      <main className={styles.map}>
        <MapView locations={locations} route={route} />
      </main>
    </div>
  );
}

function describeError(e: unknown): string {
  return e instanceof ApiError ? e.message : "Ocurrió un error inesperado.";
}
