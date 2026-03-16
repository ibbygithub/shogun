"use client";

interface EventResult {
  title: string;
  url: string;
  summary: string;
  score: number;
}

interface EventsData {
  city: string;
  results: EventResult[];
  query_time: string;
  error?: string;
}

interface Props {
  data: EventsData | null;
  loading?: boolean;
}

export default function EventsTile({ data, loading }: Props) {
  if (loading || !data) {
    return (
      <div style={{
        background: "white",
        borderRadius: "12px",
        padding: "1rem",
        boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
        color: "#94a3b8",
        fontSize: "0.85rem",
        minHeight: "80px",
        display: "flex",
        alignItems: "center",
      }}>
        {loading ? "Loading events…" : "Events unavailable"}
      </div>
    );
  }

  if (!data.results || data.results.length === 0) {
    return (
      <div style={{
        background: "white",
        borderRadius: "12px",
        padding: "1rem",
        boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
        color: "#6b7280",
        fontSize: "0.85rem",
      }}>
        No local events found for this month.
      </div>
    );
  }

  return (
    <div style={{
      background: "white",
      borderRadius: "12px",
      padding: "1rem",
      boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
    }}>
      <div style={{ fontWeight: 700, marginBottom: "0.6rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
        🎪 Local Events
        <span style={{ fontWeight: 400, fontSize: "0.75rem", color: "#6b7280", marginLeft: "0.25rem" }}>
          {data.city.charAt(0).toUpperCase() + data.city.slice(1)}
        </span>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {data.results.slice(0, 3).map((evt, i) => (
          <div
            key={evt.url}
            style={{
              borderBottom: i < Math.min(data.results.length, 3) - 1 ? "1px solid #f3f4f6" : "none",
              paddingBottom: i < Math.min(data.results.length, 3) - 1 ? "0.5rem" : 0,
            }}
          >
            <a
              href={evt.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                fontSize: "0.82rem",
                fontWeight: 600,
                color: "#1e40af",
                textDecoration: "none",
                display: "block",
                marginBottom: "0.2rem",
              }}
            >
              {evt.title}
            </a>
            <p style={{ fontSize: "0.75rem", color: "#6b7280", lineHeight: "1.4" }}>
              {evt.summary.substring(0, 160)}{evt.summary.length > 160 ? "…" : ""}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
