"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { DashboardStatus } from "@/lib/types";

const STATUS_COLORS: Record<string, string> = {
  ok:          "#10b981",
  degraded:    "#f59e0b",
  unreachable: "#ef4444",
};

export default function ShogunHealthCard() {
  const [health, setHealth] = useState<string>("checking");

  useEffect(() => {
    api.dashboard.status()
      .then((s) => setHealth((s as DashboardStatus).shogun_health))
      .catch(() => setHealth("unreachable"));
  }, []);

  const color = STATUS_COLORS[health] ?? "#94a3b8";

  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: "0.5rem",
      background: "white",
      borderRadius: "8px",
      padding: "0.625rem 1rem",
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      fontSize: "0.85rem",
    }}>
      <span style={{ width: 10, height: 10, borderRadius: "50%", background: color, display: "inline-block" }} />
      <span style={{ fontWeight: 600 }}>Shogun Core</span>
      <span style={{ color: "#6b7280", textTransform: "capitalize" }}>{health}</span>
    </div>
  );
}
