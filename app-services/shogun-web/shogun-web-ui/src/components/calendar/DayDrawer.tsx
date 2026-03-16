"use client";

import type { ItineraryLeg } from "@/lib/types";
import LegCard from "./LegCard";
import RemindersPanel from "@/components/reminders/RemindersPanel";

interface Props {
  date: string; // YYYY-MM-DD
  legs: ItineraryLeg[];
  onClose: () => void;
}

export default function DayDrawer({ date, legs, onClose }: Props) {
  const formatted = new Date(date + "T12:00:00").toLocaleDateString("en", {
    weekday: "long", month: "long", day: "numeric",
  });

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 100,
      display: "flex", alignItems: "flex-end",
    }}>
      {/* Backdrop */}
      <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.4)" }} onClick={onClose} />

      {/* Drawer */}
      <div style={{
        position: "relative",
        width: "100%",
        maxHeight: "80vh",
        background: "white",
        borderRadius: "16px 16px 0 0",
        padding: "1.25rem",
        overflowY: "auto",
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
          <h2 style={{ fontWeight: 800, fontSize: "1.1rem" }}>{formatted}</h2>
          <button onClick={onClose} style={{ background: "none", border: "none", fontSize: "1.25rem", cursor: "pointer" }}>✕</button>
        </div>

        {legs.length === 0 ? (
          <div style={{ color: "#9ca3af", fontSize: "0.875rem" }}>No activities scheduled.</div>
        ) : (
          legs.map((leg) => <LegCard key={leg.id} leg={leg} />)
        )}

        <div style={{ marginTop: "1rem" }}>
          <RemindersPanel date={date} showGlobal={false} />
        </div>
      </div>
    </div>
  );
}
