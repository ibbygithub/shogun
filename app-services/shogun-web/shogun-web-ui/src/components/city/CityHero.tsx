import type { CitySlug } from "@/lib/cities";
import { CITIES } from "@/lib/cities";
import TokyoLandmark from "./landmarks/TokyoLandmark";
import NaraLandmark from "./landmarks/NaraLandmark";
import OsakaLandmark from "./landmarks/OsakaLandmark";
import KyotoLandmark from "./landmarks/KyotoLandmark";

const LANDMARKS: Record<CitySlug, React.ComponentType> = {
  tokyo: TokyoLandmark,
  nara: NaraLandmark,
  osaka: OsakaLandmark,
  kyoto: KyotoLandmark,
};

interface CityHeroProps {
  slug: CitySlug;
}

export default function CityHero({ slug }: CityHeroProps) {
  const city = CITIES[slug];
  const Landmark = LANDMARKS[slug];

  return (
    <div className="city-hero">
      {/* Background landmark SVG */}
      <div style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "flex-end",
        paddingRight: "3rem",
        opacity: 0.18,
      }}>
        <Landmark />
      </div>

      {/* Large kanji watermark */}
      <div className="city-hero-kanji">{city.kanji}</div>

      {/* Content */}
      <div className="city-hero-content">
        <div style={{ fontSize: "0.75rem", color: "rgba(255,255,255,0.6)", marginBottom: "0.25rem", textTransform: "uppercase", letterSpacing: "0.1em" }}>
          {city.dates} · {city.nights} nights
        </div>
        <h1 style={{ fontSize: "2.5rem", fontWeight: 900, color: "white", lineHeight: 1 }}>
          {city.name}
        </h1>
        <p style={{ marginTop: "0.5rem", color: "rgba(255,255,255,0.75)", maxWidth: "480px", fontSize: "0.9rem" }}>
          {city.tagline}
        </p>
      </div>
    </div>
  );
}
