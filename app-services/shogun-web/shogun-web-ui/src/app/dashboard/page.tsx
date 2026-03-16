import TripStatusCard from "@/components/widgets/TripStatusCard";
import WeatherWidget from "@/components/widgets/WeatherWidget";
import BlossomWidget from "@/components/widgets/BlossomWidget";
import ShogunHealthCard from "@/components/widgets/ShogunHealthCard";
import RemindersPanel from "@/components/reminders/RemindersPanel";
import AmbientDashboard from "@/components/ambient/AmbientDashboard";

export default function DashboardPage() {
  const today = new Date().toISOString().split("T")[0];

  // Auto-detect city from today's date for weather
  // Mar 23–31 = Tokyo, Apr 1–2 = Nara, Apr 3–5 = Osaka, Apr 6–9 = Kyoto
  function todayCity(): string {
    const d = new Date();
    const m = d.getMonth() + 1; // 1-indexed
    const day = d.getDate();
    if (m === 3) return "tokyo";
    if (m === 4 && day <= 2) return "nara";
    if (m === 4 && day <= 5) return "osaka";
    if (m === 4 && day <= 9) return "kyoto";
    return "tokyo";
  }

  return (
    <div style={{ padding: "1.5rem", maxWidth: "900px" }}>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 900, marginBottom: "1.25rem" }}>
        将軍 Dashboard
      </h1>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
        <TripStatusCard />
        <ShogunHealthCard />
      </div>

      <AmbientDashboard />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
        <WeatherWidget city={todayCity()} />
        <BlossomWidget />
      </div>

      <div style={{ background: "white", borderRadius: "12px", padding: "1rem", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
        <h2 style={{ fontWeight: 700, fontSize: "0.9rem", marginBottom: "0.75rem" }}>Today's Reminders</h2>
        <RemindersPanel date={today} showGlobal={true} />
      </div>
    </div>
  );
}
