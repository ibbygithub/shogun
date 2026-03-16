"use client";

interface TransitData {
  city: string;
  status: "normal" | "disruption";
  alerts: string[];
  last_checked: string;
  error?: string;
}

interface Props {
  data: TransitData | null;
  loading?: boolean;
}

export default function TransitAlert({ data, loading }: Props) {
  if (loading || !data) {
    return (
      <div style={{
        borderRadius: "8px",
        padding: "0.625rem 1rem",
        background: "#f1f5f9",
        fontSize: "0.85rem",
        color: "#94a3b8",
      }}>
        {loading ? "Checking transit…" : "Transit status unavailable"}
      </div>
    );
  }

  if (data.status === "normal") {
    return (
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
        background: "#d1fae5",
        borderRadius: "8px",
        padding: "0.625rem 1rem",
        fontSize: "0.85rem",
      }}>
        <span style={{ fontSize: "1rem" }}>🚆</span>
        <span style={{ fontWeight: 600, color: "#065f46" }}>Transit — All clear</span>
        <span style={{ marginLeft: "auto", color: "#6b7280", fontSize: "0.7rem" }}>
          {data.city.charAt(0).toUpperCase() + data.city.slice(1)}
        </span>
      </div>
    );
  }

  // Disruption state
  return (
    <div style={{
      background: "#fef2f2",
      border: "1px solid #fecaca",
      borderRadius: "8px",
      padding: "0.75rem 1rem",
      fontSize: "0.85rem",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontWeight: 700, color: "#991b1b", marginBottom: "0.4rem" }}>
        <span>⚠️</span>
        <span>Transit disruption reported</span>
      </div>
      {data.alerts.slice(0, 3).map((alert, i) => (
        <div key={i} style={{ fontSize: "0.78rem", color: "#7f1d1d", padding: "0.15rem 0" }}>
          · {alert}
        </div>
      ))}
    </div>
  );
}
