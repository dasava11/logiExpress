/** Formulario para elegir origen, destino y paradas intermedias en orden. */
import type { NodeOut } from "../types/route";
import styles from "./LocationSelector.module.css";

interface Props {
  locations: NodeOut[];
  origin: string;
  destination: string;
  stops: string[]; // "" = parada aún sin seleccionar
  disabled?: boolean;
  onOriginChange: (id: string) => void;
  onDestinationChange: (id: string) => void;
  onStopsChange: (stops: string[]) => void;
  onSubmit: () => void;
}

export default function LocationSelector({
  locations,
  origin,
  destination,
  stops,
  disabled = false,
  onOriginChange,
  onDestinationChange,
  onStopsChange,
  onSubmit,
}: Props) {
  const options = locations.map((l) => (
    <option key={l.id} value={l.id}>
      {l.id} · {l.name}
    </option>
  ));

  const updateStop = (index: number, value: string) =>
    onStopsChange(stops.map((s, i) => (i === index ? value : s)));

  const removeStop = (index: number) =>
    onStopsChange(stops.filter((_, i) => i !== index));

  const moveStop = (index: number, delta: -1 | 1) => {
    const target = index + delta;
    if (target < 0 || target >= stops.length) return;
    const next = [...stops];
    [next[index], next[target]] = [next[target], next[index]];
    onStopsChange(next);
  };

  const canSubmit = !disabled && origin !== "" && destination !== "";

  return (
    <form
      className={styles.form}
      onSubmit={(e) => {
        e.preventDefault();
        if (canSubmit) onSubmit();
      }}
    >
      <div className={styles.field}>
        <label htmlFor="origin" className={styles.label}>
          Origen
        </label>
        <select
          id="origin"
          className={styles.select}
          value={origin}
          disabled={disabled}
          onChange={(e) => onOriginChange(e.target.value)}
        >
          <option value="">Selecciona…</option>
          {options}
        </select>
      </div>

      <div className={styles.stops}>
        <span className={styles.label}>Paradas intermedias (en orden)</span>
        {stops.map((stop, index) => (
          <div key={index} className={styles.stopRow}>
            <span className={styles.stopIndex}>{index + 1}</span>
            <select
              aria-label={`Parada ${index + 1}`}
              className={styles.select}
              value={stop}
              disabled={disabled}
              onChange={(e) => updateStop(index, e.target.value)}
            >
              <option value="">Selecciona…</option>
              {options}
            </select>
            <button
              type="button"
              className={styles.iconButton}
              aria-label="Subir parada"
              disabled={disabled || index === 0}
              onClick={() => moveStop(index, -1)}
            >
              ↑
            </button>
            <button
              type="button"
              className={styles.iconButton}
              aria-label="Bajar parada"
              disabled={disabled || index === stops.length - 1}
              onClick={() => moveStop(index, 1)}
            >
              ↓
            </button>
            <button
              type="button"
              className={styles.iconButton}
              aria-label="Quitar parada"
              disabled={disabled}
              onClick={() => removeStop(index)}
            >
              ✕
            </button>
          </div>
        ))}
        <button
          type="button"
          className={styles.secondaryButton}
          disabled={disabled}
          onClick={() => onStopsChange([...stops, ""])}
        >
          + Agregar parada
        </button>
      </div>

      <div className={styles.field}>
        <label htmlFor="destination" className={styles.label}>
          Destino
        </label>
        <select
          id="destination"
          className={styles.select}
          value={destination}
          disabled={disabled}
          onChange={(e) => onDestinationChange(e.target.value)}
        >
          <option value="">Selecciona…</option>
          {options}
        </select>
      </div>

      <button type="submit" className={styles.primaryButton} disabled={!canSubmit}>
        {disabled ? "Calculando…" : "Calcular ruta"}
      </button>
    </form>
  );
}
