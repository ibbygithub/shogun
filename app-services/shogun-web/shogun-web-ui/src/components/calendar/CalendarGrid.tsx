"use client";

import { useState } from "react";
import type { ItineraryLeg } from "@/lib/types";
import DayDrawer from "./DayDrawer";
import LegCard from "./LegCard";

// Generate every day from Mar 23 to Apr 9
function tripDays(): Date[] {
  const days: Date[] = [];
  const start = new Date("2026-03-23T12:00:00");
  const end = new Date("2026-04-09T12:00:00");
  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    days.push(new Date(d));
  }
  return days;
}

function dateKey(d: Date): string {
  return d.toISOString().split("T")[0];
}

interface Props {
  legs: ItineraryLeg[];
}

export default function CalendarGrid({ legs }: Props) {
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const days = tripDays();
  const todayKey = new Date().toISOString().split("T")[0];

  const legsByDate: Record<string, ItineraryLeg[]> = {};
  for (const leg of legs) {
    if (leg.date_start) {
      const key = leg.date_start;
      if (!legsByDate[key]) legsByDate[key] = [];
      legsByDate[key].push(leg);
    }
  }

  return (
    <>
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
        gap: "0.5rem",
        padding: "1rem",
      }}>
        {days.map((day) => {
          const key = dateKey(day);
          const dayLegs = legsByDate[key] ?? [];
          const isToday = key === todayKey;

          return (
            <div key={key}
              onClick={() => setSelectedDate(key)}
              style={{
                background: "white",
                borderRadius: "10px",
                padding: "0.625rem",
                cursor: "pointer",
                border: isToday ? "2px solid var(--city-accent)" : "2px solid transparent",
                boxShadow: "0 1px 3px rgba(0,0,0,0.07)",
                minHeight: "90px",
                transition: "box-shadow 0.15s",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.375rem" }}>
                <span style={{ fontWeight: 700, fontSize: "0.85rem" }}>
                  {day.toLocaleDateString("en", { month: "short", day: "numeric" })}
                </span>
                <span style={{ fontSize: "0.7rem", color: "#9ca3af" }}>
                  {day.toLocaleDateString("en", { weekday: "short" })}
                </span>
              </div>
              {dayLegs.slice(0, 2).map((leg) => (
                <LegCard key={leg.id} leg={leg} compact />
              ))}
              {dayLegs.length > 2 && (
                <div style={{ fontSize: "0.7rem", color: "#6b7280", marginTop: "2px" }}>
                  +{dayLegs.length - 2} more
                </div>
              )}
              {dayLegs.length === 0 && (
                <div style={{ fontSize: "0.75rem", color: "#d1d5db" }}>Free day</div>
              )}
            </div>
          );
        })}
      </div>

      {selectedDate && (
        <DayDrawer
          date={selectedDate}
          legs={legsByDate[selectedDate] ?? []}
          onClose={() => setSelectedDate(null)}
        />
      )}
    </>
  );
}
