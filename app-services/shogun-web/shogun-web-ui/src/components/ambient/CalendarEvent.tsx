"use client";

import type { CalendarData } from "@/lib/types";

interface Props {
  data: CalendarData | null;
}

// Convert "2026-03-23" → "Mon Mar 23"
function formatDate(dateStr: string): string {
  const d = new Date(`${dateStr}T00:00:00`);
  return d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
}

export default function CalendarEvent({ data }: Props) {
  // Pre-trip: no active event today but we have countdown info from the API
  if (!data?.event && data?.days_until_trip && data.days_until_trip > 0) {
    return (
      <div style={{
        background: "#EEF2FF",
        borderRadius: 12,
        padding: "1rem",
        borderLeft: "3px solid #6366f1",
      }}>
        <div style={{ fontWeight: 700, fontSize: "1.1rem", color: "#3730a3" }}>
          ✈️ Japan in {data.days_until_trip} day{data.days_until_trip !== 1 ? "s" : ""}
        </div>
        {data.upcoming_legs && data.upcoming_legs.length > 0 && (
          <div style={{ marginTop: "0.5rem", display: "flex", flexDirection: "column", gap: "0.25rem" }}>
            {data.upcoming_legs.map((leg) => (
              <div key={leg.leg} style={{ fontSize: "0.85rem", color: "#4338ca" }}>
                <span style={{ fontWeight: 600 }}>{formatDate(leg.date)}</span>
                {" — "}
                {leg.title}
                {leg.notes && (
                  <span style={{ color: "#6366f1" }}> · {leg.notes}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // During-trip: itinerary event for today
  if (data?.event) {
    return (
      <div style={{
        display: "flex",
        alignItems: "flex-start",
        gap: "0.6rem",
        background: data.is_holiday ? "#eff6ff" : "#f0fdf4",
        borderLeft: `3px solid ${data.is_holiday ? "#3b82f6" : "#22c55e"}`,
        borderRadius: "0 8px 8px 0",
        padding: "0.625rem 0.875rem",
        fontSize: "0.85rem",
      }}>
        <span style={{ fontSize: "1rem" }}>{data.is_holiday ? "🎌" : "📅"}</span>
        <div>
          <div style={{ fontWeight: 600, color: data.is_holiday ? "#1e40af" : "#166534" }}>
            {data.event}
          </div>
          {data.note && (
            <div style={{ fontSize: "0.75rem", color: "#6b7280", marginTop: "0.2rem" }}>
              {data.note}
            </div>
          )}
        </div>
      </div>
    );
  }

  // No data at all — render nothing
  return null;
}
