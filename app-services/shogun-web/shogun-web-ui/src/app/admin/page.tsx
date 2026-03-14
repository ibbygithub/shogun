"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { ServiceHealth } from "@/lib/types";

const STATUS_COLORS: Record<string, string> = {
  ok:          "#10b981",
  degraded:    "#f59e0b",
  unreachable: "#ef4444",
};

const STATUS_ICONS: Record<string, string> = {
  ok:          "✅",
  degraded:    "⚠️",
  unreachable: "❌",
};

export default function AdminPage() {
  const [services, setServices] = useState<ServiceHealth[]>([]);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(() => {
    setLoading(true);
    api.admin.health()
      .then((d: any) => {
        setServices(d.services);
        setLastRefresh(new Date());
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 60000);
    return () => clearInterval(interval);
  }, [refresh]);

  return (
    <div style={{ padding: "1.5rem", maxWidth: "720px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
        <h1 style={{ fontSize: "1.4rem", fontWeight: 900 }}>🔧 Service Health</h1>
        <div style={{ fontSize: "0.75rem", color: "#9ca3af" }}>
          {lastRefresh ? `Last: ${lastRefresh.toLocaleTimeString()}` : "Checking…"}
          <button onClick={refresh} style={{ marginLeft: "0.5rem", background: "none", border: "1px solid #e5e7eb",
            borderRadius: "4px", padding: "2px 8px", cursor: "pointer", fontSize: "0.75rem" }}>
            Refresh
          </button>
        </div>
      </div>

      {loading && services.length === 0 && (
        <div style={{ color: "#6b7280" }}>Checking services…</div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "0.625rem" }}>
        {services.map((svc) => (
          <div key={svc.name} style={{
            background: "white",
            borderRadius: "10px",
            padding: "1rem 1.25rem",
            boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <span style={{ fontSize: "1.25rem" }}>{STATUS_ICONS[svc.status] ?? "❓"}</span>
              <div>
                <div style={{ fontWeight: 700, textTransform: "capitalize" }}>{svc.name}</div>
                <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>
                  {new Date(svc.last_check).toLocaleTimeString()}
                </div>
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ color: STATUS_COLORS[svc.status] ?? "#6b7280", fontWeight: 700, textTransform: "capitalize" }}>
                {svc.status}
              </div>
              {svc.latency_ms !== null && (
                <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>{svc.latency_ms}ms</div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: "1rem", fontSize: "0.75rem", color: "#9ca3af" }}>
        Auto-refreshes every 60 seconds.
      </div>
    </div>
  );
}
