"use client";

import { useEffect, useState, useCallback } from "react";
import WeatherCard from "./WeatherCard";
import SakuraStatus from "./SakuraStatus";
import TransitAlert from "./TransitAlert";
import AqiBadge from "./AqiBadge";
import ExchangeRate from "./ExchangeRate";
import CalendarEvent from "./CalendarEvent";
import EventsTile from "./EventsTile";
import WindyRadar from "./WindyRadar";

// Re-export the prop types from each component so we can cast cleanly.
// These must stay in sync with the interfaces in each component file.

interface WeatherData {
  city: string; temp_c: number; conditions: string; precip_mm: number;
  wind_kmh: number; temp_max: number; temp_min: number;
  forecast: { date: string; max: number; min: number; precip: number; conditions: string }[];
  cached_at: string; error?: string;
}
interface ExchangeData {
  usd_to_jpy: number | null; jpy_1000_in_usd: number | null;
  cached_at: string; error?: string;
}
interface CalendarData {
  date: string; event: string | null; note: string | null;
  is_holiday: boolean; error?: string;
}
interface AqiData {
  city: string; aqi: number | null; category: string;
  dominant_pollutant: string | null; cached_at: string; error?: string;
}
interface SakuraData {
  city: string;
  results: { title: string; url: string; summary: string; score: number }[];
  query_time: string; error?: string;
}
interface TransitData {
  city: string; status: "normal" | "disruption";
  alerts: string[]; last_checked: string; error?: string;
}
interface EventsData {
  city: string;
  results: { title: string; url: string; summary: string; score: number }[];
  query_time: string; error?: string;
}

interface SummaryData {
  city: string;
  lat: number;
  lon: number;
  weather: WeatherData;
  exchange_rate: ExchangeData;
  calendar: CalendarData;
  aqi: AqiData;
  sakura: SakuraData;
  transit: TransitData;
  events: EventsData;
  generated_at: string;
}

// API_BASE mirrors lib/api.ts: browser uses relative /api, SSR uses env var.
const API_BASE =
  typeof window !== "undefined"
    ? "/api"
    : process.env.NEXT_PUBLIC_API_URL || "http://shogun-api.ibbytech.com";

const REFRESH_INTERVAL_MS = 10 * 60 * 1000; // 10 minutes

export default function AmbientDashboard() {
  const [data, setData] = useState<SummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);

  const fetchSummary = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/ambient/summary`, {
        headers: { "Content-Type": "application/json" },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json as SummaryData);
      setFetchError(false);
    } catch (e) {
      console.error("AmbientDashboard: failed to fetch summary", e);
      setFetchError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSummary();
    const timer = setInterval(fetchSummary, REFRESH_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [fetchSummary]);

  if (fetchError && !data) {
    return (
      <div style={{
        padding: "1rem",
        background: "#fff7ed",
        borderRadius: "12px",
        color: "#9a3412",
        fontSize: "0.85rem",
        border: "1px solid #fed7aa",
        marginBottom: "1rem",
      }}>
        Ambient data unavailable — will retry automatically.
      </div>
    );
  }

  const city = data?.city ?? "osaka";
  const lat = data?.lat ?? 34.6937;
  const lon = data?.lon ?? 135.5023;
  const hasCalendarEvent = !!(data?.calendar?.event);

  return (
    <section style={{ marginBottom: "1.5rem" }}>
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: "0.75rem",
      }}>
        <h2 style={{ fontSize: "1rem", fontWeight: 700 }}>
          Ambient — {city.charAt(0).toUpperCase() + city.slice(1)}
        </h2>
        {data?.generated_at && (
          <span style={{ fontSize: "0.7rem", color: "#94a3b8" }}>
            Updated {new Date(data.generated_at).toLocaleTimeString("en", { hour: "2-digit", minute: "2-digit" })}
          </span>
        )}
      </div>

      {(loading || hasCalendarEvent) && (
        <div style={{ marginBottom: "0.75rem" }}>
          <CalendarEvent data={data?.calendar ?? null} />
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "0.75rem" }}>
        <WeatherCard data={data?.weather ?? null} loading={loading} />
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <AqiBadge data={data?.aqi ?? null} loading={loading} />
          <ExchangeRate data={data?.exchange_rate ?? null} loading={loading} />
          <TransitAlert data={data?.transit ?? null} loading={loading} />
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "0.75rem" }}>
        <SakuraStatus data={data?.sakura ?? null} loading={loading} />
        <EventsTile data={data?.events ?? null} loading={loading} />
      </div>

      <WindyRadar lat={lat} lon={lon} city={city} />
    </section>
  );
}
