"use client";

interface SakuraResult {
  title: string;
  url: string;
  summary: string;
  score: number;
}

interface SakuraData {
  city: string;
  results: SakuraResult[];
  query_time: string;
  error?: string;
}

interface Props {
  data: SakuraData | null;
  loading?: boolean;
}

export default function SakuraStatus({ data, loading }: Props) {
  if (loading || !data) {
    return (
      <div style={{
        background: "white",
        borderRadius: "12px",
        padding: "1rem",
        boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
        minHeight: "100px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "#94a3b8",
        fontSize: "0.85rem",
      }}>
        {loading ? "Loading sakura status…" : "Sakura data unavailable"}
      </div>
    );
  }

  const top = data.results[0];

  return (
    <div style={{
      background: "white",
      borderRadius: "12px",
      padding: "1rem",
      boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
    }}>
      <div style={{ fontWeight: 700, marginBottom: "0.5rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
        🌸 Sakura Forecast
      </div>

      {!top ? (
        <div style={{ fontSize: "0.85rem", color: "#6b7280" }}>No results found.</div>
      ) : (
        <div>
          <a
            href={top.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: "0.85rem",
              fontWeight: 600,
              color: "#831843",
              textDecoration: "none",
              display: "block",
              marginBottom: "0.35rem",
              lineHeight: "1.3",
            }}
          >
            {top.title}
          </a>
          <p style={{ fontSize: "0.78rem", color: "#4b5563", lineHeight: "1.45", marginBottom: "0.5rem" }}>
            {top.summary.substring(0, 220)}{top.summary.length > 220 ? "…" : ""}
          </p>

          {/* Additional results as compact links */}
          {data.results.slice(1, 3).map((r) => (
            <a
              key={r.url}
              href={r.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: "block",
                fontSize: "0.75rem",
                color: "#6b7280",
                textDecoration: "none",
                padding: "0.2rem 0",
                borderTop: "1px solid #f3f4f6",
              }}
            >
              {r.title}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
