import { notFound } from "next/navigation";
import { CITIES, type CitySlug } from "@/lib/cities";
import { api } from "@/lib/api";
import type { ItineraryLeg, BlossomEntry } from "@/lib/types";
import CityTheme from "@/components/city/CityTheme";
import CityHero from "@/components/city/CityHero";
import WeatherWidget from "@/components/widgets/WeatherWidget";
import BlossomWidget from "@/components/widgets/BlossomWidget";
import RemindersPanel from "@/components/reminders/RemindersPanel";
import PoiCard from "@/components/pois/PoiCard";
import { Poi } from "@/lib/types";

async function getCityData(slug: string) {
  const [legs, pois, blossom] = await Promise.allSettled([
    api.itinerary.list() as Promise<ItineraryLeg[]>,
    api.pois.list(slug) as Promise<Poi[]>,
    api.blossom.list() as Promise<BlossomEntry[]>,
  ]);

  return {
    legs: legs.status === "fulfilled" ? legs.value : [],
    pois: pois.status === "fulfilled" ? pois.value.slice(0, 6) : [],
    blossom: blossom.status === "fulfilled" ? blossom.value.find((b) => b.city === slug) : null,
  };
}

export default async function CityPage({ params }: { params: { slug: string } }) {
  const slug = params.slug as CitySlug;
  if (!(slug in CITIES)) notFound();

  const city = CITIES[slug];
  const today = new Date().toISOString().split("T")[0];
  const { legs, pois, blossom } = await getCityData(slug);

  // Today's legs for this city
  const todayLegs = (legs as ItineraryLeg[]).filter(
    (l) => l.city === slug && l.date_start === today
  );

  // What to bring checklist
  const CHECKLIST = ["Passport", "Cash (¥)", "IC Card (Suica)", "Slip-on shoes", "Phone charger"];

  return (
    <div>
      <CityTheme slug={slug} />
      <CityHero slug={slug} />

      <div style={{ padding: "1.5rem", maxWidth: "900px" }}>
        {/* Context strip */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.5rem" }}>
          <WeatherWidget city={slug} />
          <div style={{ background: "white", borderRadius: "12px", padding: "1rem", boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
            <div style={{ fontWeight: 700, marginBottom: "0.5rem" }}>🌸 Blossom</div>
            {blossom ? (
              <>
                <div style={{ fontSize: "0.875rem" }}>{blossom.spot}</div>
                <span className={`blossom-${blossom.status}`}
                  style={{ display: "inline-block", marginTop: "0.375rem", padding: "2px 10px", borderRadius: "9999px", fontSize: "0.75rem" }}>
                  {blossom.status}
                </span>
                <div style={{ fontSize: "0.75rem", color: "#6b7280", marginTop: "0.25rem" }}>
                  Peak: {blossom.peak_date}
                </div>
              </>
            ) : (
              <div style={{ color: "#9ca3af", fontSize: "0.875rem" }}>No blossom data</div>
            )}
          </div>
        </div>

        {/* Today's schedule (if in city today) */}
        {todayLegs.length > 0 && (
          <div style={{ background: "white", borderRadius: "12px", padding: "1rem", marginBottom: "1.5rem", boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
            <h2 style={{ fontWeight: 700, marginBottom: "0.75rem" }}>Today in {city.name}</h2>
            {todayLegs.map((leg) => (
              <div key={leg.id} style={{ marginBottom: "0.5rem" }}>
                <div style={{ fontWeight: 600 }}>{leg.title}</div>
                {leg.address_en && <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>{leg.address_en}</div>}
              </div>
            ))}
          </div>
        )}

        {/* Top POIs */}
        {pois.length > 0 && (
          <div style={{ marginBottom: "1.5rem" }}>
            <h2 style={{ fontWeight: 700, marginBottom: "0.75rem" }}>Top Places in {city.name}</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: "0.75rem" }}>
              {pois.map((poi) => <PoiCard key={poi.id} poi={poi} />)}
            </div>
            <a href="/pois" style={{ display: "inline-block", marginTop: "0.75rem", color: "var(--city-accent)", fontSize: "0.875rem", fontWeight: 600 }}>
              View all places →
            </a>
          </div>
        )}

        {/* Reminders for city */}
        <div style={{ background: "white", borderRadius: "12px", padding: "1rem", marginBottom: "1.5rem", boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
          <h2 style={{ fontWeight: 700, marginBottom: "0.75rem" }}>Japan Tips</h2>
          <RemindersPanel showGlobal={true} />
        </div>

        {/* What to bring */}
        <div style={{ background: "white", borderRadius: "12px", padding: "1rem", boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
          <h2 style={{ fontWeight: 700, marginBottom: "0.75rem" }}>What to bring</h2>
          <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "0.375rem" }}>
            {CHECKLIST.map((item) => (
              <li key={item} style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.875rem" }}>
                <span style={{ color: "#10b981", fontWeight: 700 }}>✓</span>
                {item}
              </li>
            ))}
          </ul>
        </div>

        {/* Chat CTA */}
        <div style={{ marginTop: "1.5rem", textAlign: "center" }}>
          <a href="/chat" style={{
            display: "inline-block",
            background: "var(--city-accent)",
            color: "white",
            padding: "0.75rem 2rem",
            borderRadius: "9999px",
            fontWeight: 700,
            fontSize: "0.95rem",
            textDecoration: "none",
          }}>
            💬 Ask Shogun about {city.name}
          </a>
        </div>
      </div>
    </div>
  );
}
