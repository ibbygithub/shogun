"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface ForecastDay {
  date: string;
  max: number;
  min: number;
  precip: number;
  conditions: string;
}

interface AmbientWeatherData {
  city: string;
  temp_c: number;
  conditions: string;
  precip_mm: number;
  wind_kmh: number;
  temp_max: number;
  temp_min: number;
  forecast: ForecastDay[];
  cached_at: string;
  error?: string;
}

function conditionsIcon(conditions: string): string {
  const c = conditions.toLowerCase();
  if (c.includes("clear")) return "☀️";
  if (c.includes("mainly clear") || c.includes("partly cloudy")) return "⛅";
  if (c.includes("fog")) return "🌫️";
  if (c.includes("drizzle") || c.includes("rain")) return "🌧️";
  if (c.includes("snow")) return "❄️";
  if (c.includes("thunder")) return "⛈️";
  return "🌡️";
}

function toF(c: number): number { return Math.round(c * 9 / 5 + 32); }

type OutdoorScore = "Great" | "OK" | "Rainy";

function outdoorScore(day: ForecastDay): OutdoorScore {
  if (day.precip < 2 && day.max > 12) return "Great";
  if (day.precip < 8 || day.max > 8) return "OK";
  return "Rainy";
}

const SCORE_STYLE: Record<OutdoorScore, { bg: string; color: string; border: string }> = {
  Great: { bg: "#f0fdf4", color: "#166534", border: "#22c55e" },
  OK:    { bg: "#fefce8", color: "#854d0e", border: "#eab308" },
  Rainy: { bg: "#eff6ff", color: "#1e40af", border: "#93c5fd" },
};

interface Props {
  city: string;
}

export default function WeatherPlanner({ city }: Props) {
  const [data, setData] = useState<AmbientWeatherData | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    api.ambient.weather(city)
      .then((w) => setData(w as AmbientWeatherData))
      .catch(() => setError(true));
  }, [city]);

  if (error) {
    return (
      <div style={{ padding: "0.75rem", background: "#fee2e2", borderRadius: "8px", color: "#991b1b", fontSize: "0.8rem" }}>
        Weather planner unavailable
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ padding: "0.75rem", background: "#f1f5f9", borderRadius: "8px", color: "#64748b", fontSize: "0.8rem" }}>
        Loading forecast…
      </div>
    );
  }

  // Show up to 5 forecast days starting from today (index 0)
  const days = data.forecast.slice(0, 5);

  return (
    <div style={{
      background: "white",
      borderRadius: "12px",
      padding: "1rem",
      boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
    }}>
      <div style={{ fontSize: "0.7rem", color: "#94a3b8", marginBottom: "0.5rem", textTransform: "uppercase", letterSpacing: "0.06em" }}>
        5-Day Outdoor Planner · {city.charAt(0).toUpperCase() + city.slice(1)}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
        {days.map((day) => {
          const score = outdoorScore(day);
          const style = SCORE_STYLE[score];
          const label = new Date(day.date + "T12:00:00").toLocaleDateString("en", { weekday: "short", month: "short", day: "numeric" });
          return (
            <div key={day.date} style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              background: style.bg,
              borderRadius: "8px",
              padding: "0.4rem 0.6rem",
              borderLeft: `3px solid ${style.border}`,
            }}>
              <span style={{ fontSize: "1.1rem", minWidth: "1.5rem" }}>{conditionsIcon(day.conditions)}</span>
              <span style={{ fontSize: "0.8rem", fontWeight: 600, minWidth: "5.5rem", color: "#374151" }}>{label}</span>
              <span style={{ fontSize: "0.75rem", color: "#6b7280", minWidth: "5rem" }}>
                ↑{toF(day.max)}°F ↓{toF(day.min)}°F
              </span>
              {day.precip > 0 && (
                <span style={{ fontSize: "0.7rem", color: "#3b82f6", minWidth: "3.5rem" }}>
                  💧 {day.precip}mm
                </span>
              )}
              <span style={{
                marginLeft: "auto",
                fontSize: "0.7rem",
                fontWeight: 700,
                color: style.color,
                background: style.bg,
                border: `1px solid ${style.border}`,
                borderRadius: "999px",
                padding: "0.1rem 0.5rem",
              }}>
                {score}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
