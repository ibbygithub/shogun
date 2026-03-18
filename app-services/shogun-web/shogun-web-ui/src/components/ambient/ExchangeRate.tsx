"use client";

interface ExchangeData {
  usd_to_jpy: number | null;
  jpy_1000_in_usd: number | null;
  cached_at: string;
  error?: string;
}

interface Props {
  data: ExchangeData | null;
  loading?: boolean;
}

export default function ExchangeRate({ data, loading }: Props) {
  if (loading || !data || data.usd_to_jpy === null) {
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
        color: "#94a3b8",
      }}>
        {loading ? "Loading exchange rate…" : "Rate unavailable"}
      </div>
    );
  }

  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: "0.75rem",
      background: "white",
      borderRadius: "8px",
      padding: "0.625rem 1rem",
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
    }}>
      <span style={{ fontSize: "1.1rem" }}>💴</span>
      <div>
        <div style={{ fontWeight: 700, fontSize: "0.9rem" }}>
          ¥1,000 ≈ ${data.jpy_1000_in_usd?.toFixed(2)}
        </div>
        <div style={{ fontSize: "0.72rem", color: "#6b7280" }}>
          $1 = ¥{data.usd_to_jpy?.toFixed(2)}
        </div>
      </div>
    </div>
  );
}
