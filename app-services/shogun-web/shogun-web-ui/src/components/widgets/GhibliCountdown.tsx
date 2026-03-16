"use client";

export default function GhibliCountdown() {
  const ghibliDate = new Date("2026-04-03T12:00:00+09:00");
  const now = new Date();
  const diff = ghibliDate.getTime() - now.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

  if (diff <= 0) {
    return (
      <div style={{ background: "#f0fdf4", borderRadius: 12, padding: "1rem", marginBottom: "1rem", borderLeft: "3px solid #22c55e" }}>
        <div style={{ fontWeight: 700, color: "#166534" }}>🎬 Ghibli Museum — Today! Timed entry at noon</div>
      </div>
    );
  }
  return (
    <div style={{ background: "#fef3c7", borderRadius: 12, padding: "1rem", marginBottom: "1rem", borderLeft: "3px solid #f59e0b" }}>
      <div style={{ fontWeight: 700, color: "#92400e", fontSize: "0.9rem" }}>
        🎬 Ghibli Museum
      </div>
      <div style={{ fontSize: "1.4rem", fontWeight: 900, color: "#78350f" }}>
        {days}d {hours}h away
      </div>
      <div style={{ fontSize: "0.75rem", color: "#92400e", marginTop: "0.25rem" }}>
        April 3 · Timed entry noon · Mitaka station
      </div>
    </div>
  );
}
