"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Poi } from "@/lib/types";
import PoiCard from "@/components/pois/PoiCard";
import CityTabs from "@/components/pois/CityTabs";
import FilterBar from "@/components/pois/FilterBar";

export default function PoisPage() {
  const [pois, setPois] = useState<Poi[]>([]);
  const [activeCity, setActiveCity] = useState("all");
  const [activeTags, setActiveTags] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const city = activeCity === "all" ? undefined : activeCity;
    api.pois.list(city, activeTags)
      .then((d) => setPois(d as Poi[]))
      .finally(() => setLoading(false));
  }, [activeCity, activeTags]);

  return (
    <div>
      <div style={{ padding: "1.25rem 1rem 0" }}>
        <h1 style={{ fontSize: "1.4rem", fontWeight: 900 }}>Places of Interest</h1>
      </div>

      <CityTabs active={activeCity} onChange={setActiveCity} />
      <FilterBar active={activeTags} onChange={setActiveTags} />

      <div style={{ padding: "0.75rem 1rem" }}>
        {loading ? (
          <div style={{ color: "#6b7280" }}>Loading places…</div>
        ) : pois.length === 0 ? (
          <div style={{ color: "#9ca3af" }}>No places found.</div>
        ) : (
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
            gap: "0.75rem",
          }}>
            {pois.map((poi) => <PoiCard key={poi.id} poi={poi} />)}
          </div>
        )}
      </div>
    </div>
  );
}
