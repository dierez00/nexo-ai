/**
 * Historial ligero de folios completados, en `localStorage`, para las
 * páginas de trámite/seguimiento: no hay endpoint de "mis folios", así que el
 * chat persiste cada confirmación aquí cuando ocurre.
 */

const FOLIO_HISTORY_KEY = "nexo.chat.folios";

export type FolioEntry = {
  run_id: string;
  folio: string;
  label: string;
  completed_at: string;
};

export function persistFolio(entry: FolioEntry) {
  if (typeof window === "undefined") return;
  const list = readFolioHistory();
  window.localStorage.setItem(FOLIO_HISTORY_KEY, JSON.stringify([entry, ...list].slice(0, 20)));
}

export function readFolioHistory(): FolioEntry[] {
  if (typeof window === "undefined") return [];
  const raw = window.localStorage.getItem(FOLIO_HISTORY_KEY);
  if (!raw) return [];
  try {
    return JSON.parse(raw) as FolioEntry[];
  } catch {
    return [];
  }
}

export function readFolioFor(runId: string): FolioEntry | undefined {
  return readFolioHistory().find((entry) => entry.run_id === runId);
}
