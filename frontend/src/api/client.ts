import type {
  CreateDatePayload,
  DateEvent,
  HitlistRestaurant,
  User,
  VenueResult,
} from "../types";

// In production (Vercel), VITE_API_URL points to the Render backend.
// In development, the Vite proxy handles /api → localhost:8000.
const BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : "/api";

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...init?.headers,
    },
    ...init,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export const authApi = {
  register: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  login: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<User>("/auth/me"),

  updateCredentials: (resy_email: string, resy_password: string, resy_api_key: string) =>
    request<User>("/auth/credentials", {
      method: "PUT",
      body: JSON.stringify({ resy_email, resy_password, resy_api_key }),
    }),
};

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

  update: (id: number, payload: Omit<CreateDatePayload, "restaurant_id">) =>
    request<DateEvent>(`/dates/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  cancel: (id: number) =>
    request<DateEvent>(`/dates/${id}/cancel`, { method: "POST" }),

  delete: (id: number) =>
    request<void>(`/dates/${id}`, { method: "DELETE" }),
};

// ── Restaurants ───────────────────────────────────────────────────────────────

export const restaurantsApi = {
  search: (q: string, page = 1) =>
    request<{ results: VenueResult[]; page: number; total_pages: number; total: number }>(
      `/restaurants/search?q=${encodeURIComponent(q)}&page=${page}`
    ),
};
