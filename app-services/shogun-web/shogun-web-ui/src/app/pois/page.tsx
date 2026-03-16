"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Poi } from "@/lib/types";
import PoiCard from "@/components/pois/PoiCard";
import CityTabs from "@/components/pois/CityTabs";
import FilterBar from "@/components/pois/FilterBar";
import PoisMap from "@/components/pois/PoisMap";

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

  // POIs with coordinates — map only shows when a specific city is selected and coords are available
  const mappablePois = pois.filter(
    (p) => typeof p.lat === "number" && p.lat !== null &&
           typeof p.lng === "number" && p.lng !== null
  );
  const showMap = activeCity !== "all" && mappablePois.length > 0;

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
        ) : showMap ? (
          /* City selected + mappable POIs: side-by-side layout */
          <div style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "1rem",
            alignItems: "start",
          }}>
            {/* POI tiles — left column, scrollable */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "1fr",
              gap: "0.75rem",
              maxHeight: "calc(100vh - 220px)",
              overflowY: "auto",
              paddingRight: "0.25rem",
            }}>
              {pois.map((poi) => <PoiCard key={poi.id} poi={poi} />)}
            </div>
            {/* Map — right column, sticky */}
            <div style={{ position: "sticky", top: "1rem" }}>
              <PoisMap pois={pois} city={activeCity} />
            </div>
          </div>
        ) : (
          /* No map: standard grid */
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
            gap: "0.75rem",
          }}>
            {pois.map((poi) => <PoiCard key={poi.id} poi={poi} />)}
          </div>
        )}
      </div>

      {/* Mobile: show map below tiles when a city is selected */}
      <style>{`
        @media (max-width: 767px) {
          .pois-map-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
}
