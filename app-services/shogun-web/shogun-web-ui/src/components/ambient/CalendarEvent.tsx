"use client";

interface CalendarData {
  date: string;
  event: string | null;
  note: string | null;
  is_holiday: boolean;
  error?: string;
}

interface Props {
  data: CalendarData | null;
}

export default function CalendarEvent({ data }: Props) {
  // Render nothing if there is no event today
  if (!data || !data.event) return null;

  return (
    <div style={{
      display: "flex",
      alignItems: "flex-start",
      gap: "0.6rem",
      background: data.is_holiday ? "#eff6ff" : "#f0fdf4",
      borderLeft: `3px solid ${data.is_holiday ? "#3b82f6" : "#22c55e"}`,
      borderRadius: "0 8px 8px 0",
      padding: "0.625rem 0.875rem",
      fontSize: "0.85rem",
    }}>
      <span style={{ fontSize: "1rem" }}>{data.is_holiday ? "🎌" : "📅"}</span>
      <div>
        <div style={{ fontWeight: 600, color: data.is_holiday ? "#1e40af" : "#166534" }}>
          {data.event}
        </div>
        {data.note && (
          <div style={{ fontSize: "0.75rem", color: "#6b7280", marginTop: "0.2rem" }}>
            {data.note}
          </div>
        )}
      </div>
    </div>
  );
}
