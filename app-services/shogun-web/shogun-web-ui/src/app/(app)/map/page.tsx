import TripMap from "@/components/map/TripMap";

export default function MapPage() {
  return (
    <div style={{ padding: "1.5rem", maxWidth: "1400px" }}>
      <h1 style={{ fontWeight: 800, fontSize: "1.5rem", marginBottom: "0.25rem" }}>
        🗺️ Trip Map
      </h1>
      <p style={{ color: "#6b7280", fontSize: "0.875rem", marginBottom: "1.25rem" }}>
        Full itinerary mapped by city · Mar 23 – Apr 9, 2026 · Click any pin for details
      </p>

      <TripMap height="calc(100vh - 180px)" />
    </div>
  );
}
