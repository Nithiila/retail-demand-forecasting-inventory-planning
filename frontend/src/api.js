
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api/v1";

export async function fetchJson(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json();
}

export const api = {
  forecasts: (params = "") => fetchJson(`/forecasts${params}`),
  demandHistory: (params = "") => fetchJson(`/demand-history${params}`),
  products: () => fetchJson("/products"),
  stores: () => fetchJson("/stores"),
  inventory: () => fetchJson("/inventory"),
  risks: () => fetchJson("/inventory/risks"),
  recommendations: () => fetchJson("/inventory/recommendations"),
};
