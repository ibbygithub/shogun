"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { WeatherResponse } from "@/lib/types";

const WMO_ICONS: Record<number, string> = {
  0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️",
  45: "🌫️", 48: "🌫️",
  51: "🌦️", 53: "🌦️", 55: "🌧️",
  61: "🌧️", 63: "🌧️", 65: "🌧️",
  71: "🌨️", 73: "🌨️", 75: "❄️",
  80: "🌦️", 81: "🌧️", 82: "⛈️",
  95: "⛈️", 96: "⛈️", 99: "⛈️",
};

function wmoIcon(code: number): string {
  return WMO_ICONS[code] ?? "🌡️";
}

// Convert Celsius to Fahrenheit, rounded to nearest integer
function toF(c: number): number { return Math.round(c * 9/5 + 32); }

interface Props {
  city: string;
}

export default function WeatherWidget({ city }: Props) {
  const [weather, setWeather] = useState<WeatherResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    api.weather.get(city)
      .then((w) => setWeather(w as WeatherResponse))
      .catch(() => setError(true));
  }, [city]);

  if (error) {
    return (
      <div style={{ padding: "1rem", background: "#fee2e2", borderRadius: "8px", color: "#991b1b" }}>
        Weather unavailable
      </div>
    );
  }

  if (!weather) {
    return (
      <div style={{ padding: "1rem", background: "#f1f5f9", borderRadius: "8px", color: "#64748b" }}>
        Loading weather…
      </div>
    );
  }

  return (
    <div style={{ background: "white", borderRadius: "12px", padding: "1rem", boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
      {/* Current */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.75rem" }}>
        <span style={{ fontSize: "2.5rem" }}>{wmoIcon(weather.current.weather_code)}</span>
        <div>
          <div style={{ fontSize: "1.75rem", fontWeight: 700, lineHeight: 1 }}>
            {toF(weather.current.temperature_2m)}°F
          </div>
          <div style={{ fontSize: "0.85rem", color: "#6b7280", lineHeight: 1.2 }}>
            {Math.round(weather.current.temperature_2m)}°C
          </div>
          <div style={{ fontSize: "0.75rem", color: "#6b7280", marginTop: "0.15rem" }}>
            Wind {Math.round(weather.current.wind_speed_10m)} km/h
          </div>
        </div>
      </div>

      {/* 3-day forecast */}
      <div style={{ display: "flex", gap: "0.5rem" }}>
        {weather.forecast_3day.map((day) => (
          <div key={day.date} style={{
            flex: 1, textAlign: "center", background: "#f8fafc", borderRadius: "8px", padding: "0.5rem",
          }}>
            <div style={{ fontSize: "0.7rem", color: "#6b7280" }}>
              {new Date(day.date + "T12:00:00").toLocaleDateString("en", { weekday: "short" })}
            </div>
            <div style={{ fontSize: "1.25rem" }}>{wmoIcon(day.weather_code)}</div>
            <div style={{ fontSize: "0.75rem", fontWeight: 600 }}>{toF(day.temperature_max)}°F</div>
            <div style={{ fontSize: "0.7rem", color: "#94a3b8" }}>{toF(day.temperature_min)}°F</div>
          </div>
        ))}
      </div>
    </div>
  );
}
