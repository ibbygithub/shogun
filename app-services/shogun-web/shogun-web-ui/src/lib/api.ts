const API_BASE =
  typeof window !== "undefined"
    ? "/api" // browser: rewrite via next.config.js
    : process.env.NEXT_PUBLIC_API_URL || "http://shogun-api.ibbytech.com";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${path} → ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  dashboard: {
    status: () => apiFetch("/dashboard/status"),
  },
  calendar: {
    list: () => apiFetch("/calendar"),
  },
  itinerary: {
    list: () => apiFetch("/itinerary"),
    create: (body: unknown) =>
      apiFetch("/itinerary", { method: "POST", body: JSON.stringify(body) }),
    update: (id: number, body: unknown) =>
      apiFetch(`/itinerary/${id}`, { method: "PUT", body: JSON.stringify(body) }),
    delete: (id: number) =>
      apiFetch(`/itinerary/${id}`, { method: "DELETE" }),
  },
  pois: {
    list: (city?: string, tags?: string[]) => {
      const params = new URLSearchParams();
      if (city) params.set("city", city);
      tags?.forEach((t) => params.append("tags", t));
      return apiFetch(`/pois?${params}`);
    },
    knowledge: (id: number) => apiFetch(`/pois/${id}/knowledge`),
  },
  weather: {
    get: (city: string) => apiFetch(`/weather?city=${city}`),
  },
  blossom: {
    list: () => apiFetch("/blossom"),
  },
  reminders: {
    get: (date?: string) =>
      apiFetch(`/reminders${date ? `?date=${date}` : ""}`),
  },
  wishlist: {
    list: () => apiFetch("/wishlist"),
    create: (body: { city?: string; description: string }) =>
      apiFetch("/wishlist", { method: "POST", body: JSON.stringify(body) }),
    approve: (id: number, note?: string) =>
      apiFetch(`/wishlist/${id}/approve`, {
        method: "PUT",
        body: JSON.stringify({ itinerary_note: note }),
      }),
    reject: (id: number) =>
      apiFetch(`/wishlist/${id}/reject`, { method: "PUT", body: "{}" }),
  },
  chat: {
    send: (message: string) =>
      apiFetch("/chat", { method: "POST", body: JSON.stringify({ message }) }),
    history: () => apiFetch("/chat/history"),
  },
  ambient: {
    summary: () => apiFetch("/api/ambient/summary"),
    weather: (city: string) => apiFetch(`/api/ambient/weather/${city}`),
    sakura: (city: string) => apiFetch(`/api/ambient/sakura/${city}`),
    transit: (city: string) => apiFetch(`/api/ambient/transit/${city}`),
    events: (city: string) => apiFetch(`/api/ambient/events/${city}`),
    aqi: (city: string) => apiFetch(`/api/ambient/aqi/${city}`),
    exchangeRate: () => apiFetch("/api/ambient/exchange-rate"),
    calendar: () => apiFetch("/api/ambient/calendar"),
  },
  planning: {
    itinerary: () => apiFetch<Record<string, unknown[]>>("/planning/itinerary"),
    schedule: (body: { date: string; poi_name: string; city: string; notes: string }) =>
      apiFetch("/planning/schedule", { method: "POST", body: JSON.stringify(body) }),
  },
  budget: {
    list: () => apiFetch<{ items: import("./types").BudgetItem[]; total_jpy: number; by_category: Record<string, number> }>("/api/budget"),
    add: (body: { trip_date?: string; category: string; description: string; amount_jpy: number }) =>
      apiFetch<import("./types").BudgetItem>("/api/budget", { method: "POST", body: JSON.stringify(body) }),
    remove: (id: number) => apiFetch<{ ok: boolean }>(`/api/budget/${id}`, { method: "DELETE" }),
  },
  admin: {
    health: () => apiFetch("/admin/health"),
  },
  settings: {
    preferences: () => apiFetch("/settings/preferences"),
    setPreference: (type: string, value: string) =>
      apiFetch("/settings/preferences", {
        method: "PUT",
        body: JSON.stringify({ preference_type: type, preference_value: value }),
      }),
    users: () => apiFetch("/settings/users"),
  },
};
