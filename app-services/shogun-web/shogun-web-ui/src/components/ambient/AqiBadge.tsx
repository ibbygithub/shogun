"use client";

interface AqiData {
  city: string;
  aqi: number | null;
  category: string;
  dominant_pollutant: string | null;
  cached_at: string;
  error?: string;
}

interface Props {
  data: AqiData | null;
  loading?: boolean;
}

function aqiColor(category: string): { bg: string; text: string; dot: string } {
  switch (category) {
    case "Good":
      return { bg: "#d1fae5", text: "#065f46", dot: "#10b981" };
    case "Moderate":
      return { bg: "#fef9c3", text: "#713f12", dot: "#f59e0b" };
    case "Unhealthy for Sensitive Groups":
      return { bg: "#ffedd5", text: "#9a3412", dot: "#f97316" };
    case "Unhealthy":
      return { bg: "#fee2e2", text: "#991b1b", dot: "#ef4444" };
    case "Very Unhealthy":
      return { bg: "#f3e8ff", text: "#6b21a8", dot: "#a855f7" };
    case "Hazardous":
      return { bg: "#1f2937", text: "#f9fafb", dot: "#7c3aed" };
    default:
      return { bg: "#f1f5f9", text: "#64748b", dot: "#94a3b8" };
  }
}

export default function AqiBadge({ data, loading }: Props) {
  if (loading || !data) {
    return (
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
        background: "#f1f5f9",
        borderRadius: "8px",
        padding: "0.5rem 0.75rem",
        fontSize: "0.85rem",
        color: "#94a3b8",
      }}>
        {loading ? "Checking AQI…" : "AQI unavailable"}
      </div>
    );
  }

  const colors = aqiColor(data.category);

  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: "0.6rem",
      background: colors.bg,
      borderRadius: "8px",
      padding: "0.5rem 0.75rem",
      fontSize: "0.85rem",
    }}>
      <span style={{
        width: 10,
        height: 10,
        borderRadius: "50%",
        background: colors.dot,
        flexShrink: 0,
        display: "inline-block",
      }} />
      <span style={{ fontWeight: 600, color: colors.text }}>AQI</span>
      {data.aqi !== null ? (
        <span style={{
          fontWeight: 700,
          fontSize: "1.1rem",
          color: colors.text,
          lineHeight: 1,
        }}>
          {data.aqi}
        </span>
      ) : null}
      <span style={{ color: colors.text, fontSize: "0.8rem" }}>{data.category}</span>
      {data.dominant_pollutant && data.dominant_pollutant !== "unknown" && (
        <span style={{ marginLeft: "auto", color: colors.text, fontSize: "0.7rem", opacity: 0.75 }}>
          {data.dominant_pollutant.toUpperCase()}
        </span>
      )}
    </div>
  );
}
