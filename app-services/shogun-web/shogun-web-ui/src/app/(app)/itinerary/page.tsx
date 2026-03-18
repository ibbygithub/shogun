"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ItineraryLeg } from "@/lib/types";
import LegCard from "@/components/calendar/LegCard";

export default function ItineraryPage() {
  const [legs, setLegs] = useState<ItineraryLeg[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.itinerary.list()
      .then((d) => setLegs(d as ItineraryLeg[]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ padding: "1.5rem", maxWidth: "800px" }}>
      <h1 style={{ fontSize: "1.4rem", fontWeight: 900, marginBottom: "1.25rem" }}>Full Itinerary</h1>

      {loading && <div style={{ color: "#6b7280" }}>Loading…</div>}

      {!loading && legs.length === 0 && (
        <div style={{ color: "#9ca3af" }}>No itinerary items yet.</div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {legs.map((leg) => (
          <div key={leg.id}>
            {leg.date_start && (
              <div style={{ fontSize: "0.75rem", color: "#9ca3af", margin: "0.5rem 0 0.25rem",
                textTransform: "uppercase", letterSpacing: "0.06em" }}>
                {new Date(leg.date_start + "T12:00:00").toLocaleDateString("en",
                  { weekday: "short", month: "short", day: "numeric" })}
              </div>
            )}
            <LegCard leg={leg} />
          </div>
        ))}
      </div>
    </div>
  );
}
