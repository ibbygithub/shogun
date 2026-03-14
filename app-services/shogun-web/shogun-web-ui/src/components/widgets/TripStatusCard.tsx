"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { DashboardStatus } from "@/lib/types";
import { CITIES } from "@/lib/cities";

export default function TripStatusCard() {
  const [status, setStatus] = useState<DashboardStatus | null>(null);

  useEffect(() => {
    api.dashboard.status().then((s) => setStatus(s as DashboardStatus));
  }, []);

  if (!status) return null;

  const departure = new Date(status.departure_date);
  const today = new Date();
  const daysUntil = Math.ceil((departure.getTime() - today.getTime()) / 86400000);
  const cityName = status.current_city
    ? CITIES[status.current_city as keyof typeof CITIES]?.name ?? status.current_city
    : null;

  return (
    <div style={{
      background: "linear-gradient(135deg, var(--city-primary), color-mix(in srgb, var(--city-primary) 70%, var(--city-accent)))",
      borderRadius: "12px",
      padding: "1.25rem",
      color: "white",
    }}>
      {status.trip_day ? (
        <>
          <div style={{ fontSize: "0.75rem", color: "rgba(255,255,255,0.65)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Currently in
          </div>
          <div style={{ fontSize: "1.75rem", fontWeight: 800, marginTop: "0.25rem" }}>{cityName}</div>
          <div style={{ fontSize: "0.875rem", color: "rgba(255,255,255,0.75)", marginTop: "0.25rem" }}>
            Day {status.trip_day} of {status.total_days}
          </div>
        </>
      ) : daysUntil > 0 ? (
        <>
          <div style={{ fontSize: "0.75rem", color: "rgba(255,255,255,0.65)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Japan trip in
          </div>
          <div style={{ fontSize: "2.5rem", fontWeight: 900, marginTop: "0.125rem" }}>{daysUntil}</div>
          <div style={{ fontSize: "0.875rem", color: "rgba(255,255,255,0.75)" }}>days</div>
        </>
      ) : (
        <div style={{ fontSize: "1.1rem", fontWeight: 700 }}>Trip complete 🎌</div>
      )}

      {status.pending_wishlist_count > 0 && (
        <div style={{
          marginTop: "0.75rem",
          background: "rgba(255,255,255,0.15)",
          borderRadius: "6px",
          padding: "0.4rem 0.75rem",
          fontSize: "0.8rem",
          display: "inline-block",
        }}>
          ⭐ {status.pending_wishlist_count} wishlist item{status.pending_wishlist_count !== 1 ? "s" : ""} pending
        </div>
      )}
    </div>
  );
}
