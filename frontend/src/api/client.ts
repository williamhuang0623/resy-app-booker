import type {
  CreateDatePayload,
  DateEvent,
  HitlistRestaurant,
  VenueResult,
} from "../types";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Hitlist ──────────────────────────────────────────────────────────────────

export const hitlistApi = {
  list: () => request<HitlistRestaurant[]>("/hitlist/"),

  add: (venue: VenueResult) =>
    request<HitlistRestaurant>("/hitlist/", {
      method: "POST",
      body: JSON.stringify(venue),
    }),

  remove: (id: number) =>
    request<void>(`/hitlist/${id}`, { method: "DELETE" }),
};

// ── Dates ─────────────────────────────────────────────────────────────────────

export const datesApi = {
  list: () => request<DateEvent[]>("/dates/"),

  create: (payload: CreateDatePayload) =>
    request<DateEvent>("/dates/", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  monitor: (id: number) =>
    request<DateEvent>(`/dates/${id}/monitor`, { method: "POST" }),

  cancel: (id: number) =>
    request<DateEvent>(`/dates/${id}/cancel`, { method: "POST" }),

  delete: (id: number) =>
    request<void>(`/dates/${id}`, { method: "DELETE" }),
};

// ── Restaurants ───────────────────────────────────────────────────────────────

export const restaurantsApi = {
  search: (q: string, lat?: number, lon?: number) => {
    const params = new URLSearchParams({ q });
    if (lat !== undefined) params.set("lat", String(lat));
    if (lon !== undefined) params.set("lon", String(lon));
    return request<VenueResult[]>(`/restaurants/search?${params}`);
  },
};
