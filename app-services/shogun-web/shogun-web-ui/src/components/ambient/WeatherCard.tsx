"use client";

import { useEffect, useState } from "react";

// WMO code → emoji icon — consistent with existing WeatherWidget
const WMO_ICONS: Record<number, string> = {
  0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️",
  45: "🌫️", 48: "🌫️",
  51: "🌦️", 53: "🌦️", 55: "🌧️",
  61: "🌧️", 63: "🌧️", 65: "🌧️",
  71: "🌨️", 73: "🌨️", 75: "❄️",
  80: "🌦️", 81: "🌧️", 82: "⛈️",
  95: "⛈️", 96: "⛈️", 99: "⛈️",
};

// The ambient weather endpoint returns a text description, not a WMO code.
// Map common phrases to icons for display.
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

// Convert Celsius to Fahrenheit, rounded to nearest integer
function toF(c: number): number { return Math.round(c * 9/5 + 32); }

interface ForecastDay {
  date: string;
  max: number;
  min: number;
  precip: number;
  conditions: string;
}

interface WeatherData {
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

interface Props {
  data: WeatherData | null;
  loading?: boolean;
}

export default function WeatherCard({ data, loading }: Props) {
  if (loading || !data) {
    return (
      <div style={{
        background: "white",
        borderRadius: "12px",
        padding: "1rem",
        boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
        minHeight: "140px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "#94a3b8",
        fontSize: "0.85rem",
      }}>
        {loading ? "Loading weather…" : "Weather unavailable"}
      </div>
    );
  }

  if (data.error) {
    return (
      <div style={{
        background: "#fee2e2",
        borderRadius: "12px",
        padding: "1rem",
        color: "#991b1b",
        fontSize: "0.85rem",
      }}>
        Weather unavailable
      </div>
    );
  }

  const icon = conditionsIcon(data.conditions);
  // Show up to 3 forecast days (skip today = index 0)
  const forecastDays = data.forecast.slice(1, 4);

  return (
    <div style={{
      background: "white",
      borderRadius: "12px",
      padding: "1rem",
      boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
    }}>
      <div style={{ fontSize: "0.7rem", color: "#94a3b8", marginBottom: "0.5rem", textTransform: "uppercase", letterSpacing: "0.06em" }}>
        Weather · {data.city.charAt(0).toUpperCase() + data.city.slice(1)}
      </div>

      {/* Current conditions */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }}>
        <span style={{ fontSize: "2.25rem" }}>{icon}</span>
        <div>
          <div style={{ fontSize: "1.75rem", fontWeight: 700, lineHeight: 1 }}>
            {toF(data.temp_c)}°F
          </div>
          <div style={{ fontSize: "0.85rem", color: "#6b7280", lineHeight: 1.2 }}>
            {Math.round(data.temp_c)}°C
          </div>
          <div style={{ fontSize: "0.75rem", color: "#6b7280", marginTop: "0.15rem" }}>
            {data.conditions}
          </div>
        </div>
        <div style={{ marginLeft: "auto", textAlign: "right" }}>
          <div style={{ fontSize: "0.8rem", fontWeight: 600 }}>
            ↑{toF(data.temp_max)}°F ↓{toF(data.temp_min)}°F
          </div>
          {data.precip_mm > 0 && (
            <div style={{ fontSize: "0.75rem", color: "#3b82f6" }}>
              💧 {data.precip_mm}mm
            </div>
          )}
          <div style={{ fontSize: "0.7rem", color: "#94a3b8" }}>
            {Math.round(data.wind_kmh)} km/h
          </div>
        </div>
      </div>

      {/* 3-day strip */}
      {forecastDays.length > 0 && (
        <div style={{ display: "flex", gap: "0.4rem" }}>
          {forecastDays.map((day) => (
            <div
              key={day.date}
              style={{
                flex: 1,
                textAlign: "center",
                background: "#f8fafc",
                borderRadius: "8px",
                padding: "0.4rem 0.25rem",
              }}
            >
              <div style={{ fontSize: "0.65rem", color: "#6b7280" }}>
                {new Date(day.date + "T12:00:00").toLocaleDateString("en", { weekday: "short" })}
              </div>
              <div style={{ fontSize: "1.1rem" }}>{conditionsIcon(day.conditions)}</div>
              <div style={{ fontSize: "0.75rem", fontWeight: 600 }}>{toF(day.max)}°F</div>
              <div style={{ fontSize: "0.65rem", color: "#94a3b8" }}>{toF(day.min)}°F</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
