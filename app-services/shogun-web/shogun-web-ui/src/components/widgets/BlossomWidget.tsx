"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { BlossomEntry } from "@/lib/types";
import { CITIES } from "@/lib/cities";

const STATUS_LABELS: Record<string, string> = {
  not_started: "Not started",
  early:       "Early bloom",
  peak:        "Peak ✨",
  late:        "Late bloom",
  finished:    "Finished",
};

export default function BlossomWidget() {
  const [entries, setEntries] = useState<BlossomEntry[]>([]);

  useEffect(() => {
    api.blossom.list().then((d) => setEntries(d as BlossomEntry[]));
  }, []);

  if (!entries.length) return null;

  return (
    <div style={{ background: "white", borderRadius: "12px", padding: "1rem", boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
      <div style={{ fontWeight: 700, marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
        🌸 Cherry Blossom Tracker
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {entries.map((e) => {
          const city = CITIES[e.city as keyof typeof CITIES];
          return (
            <div key={e.city} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: "0.85rem" }}>
              <div>
                <span style={{ fontWeight: 600 }}>{city?.name ?? e.city}</span>
                <span style={{ color: "#6b7280", marginLeft: "0.25rem" }}>· {e.spot}</span>
              </div>
              <span className={`blossom-${e.status}`} style={{ padding: "2px 8px", borderRadius: "9999px", fontSize: "0.75rem" }}>
                {STATUS_LABELS[e.status] ?? e.status}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
