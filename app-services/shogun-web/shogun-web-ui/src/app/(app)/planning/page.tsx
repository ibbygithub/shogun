"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Poi, ItineraryLeg } from "@/lib/types";
import dynamic from "next/dynamic";

const TripMap = dynamic(() => import("@/components/map/TripMap"), {
  ssr: false,
  loading: () => (
    <div style={{ height: "450px", background: "#f1f5f9", borderRadius: "12px", display: "flex", alignItems: "center", justifyContent: "center", color: "#9ca3af", fontSize: "0.875rem" }}>
      Loading map…
    </div>
  ),
});

// Trip schedule: date key → city name
function cityForDate(key: string): string {
  if (key === "2026-03-23") return "travel";
  if (key >= "2026-03-24" && key <= "2026-03-29") return "osaka";
  if (key >= "2026-03-30" && key <= "2026-03-31") return "kanazawa";
  if (key >= "2026-04-01" && key <= "2026-04-09") return "tokyo";
  return "travel";
}

const CITY_BG: Record<string, string> = {
  osaka: "#FFF3E0",
  kanazawa: "#E8F5E9",
  tokyo: "#E3F2FD",
  travel: "#F3F4F6",
};

const CITY_LABEL: Record<string, string> = {
  osaka: "🏯 Osaka",
  kanazawa: "🌸 Kanazawa",
  tokyo: "🗼 Tokyo",
  travel: "✈️ Travel",
};

const CITY_BADGE_COLOR: Record<string, string> = {
  osaka: "#d97706",
  kanazawa: "#16a34a",
  tokyo: "#2563eb",
  travel: "#6b7280",
};

// All 18 trip days in order
function tripDays(): string[] {
  const days: string[] = [];
  const start = new Date("2026-03-23T12:00:00");
  const end = new Date("2026-04-09T12:00:00");
  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    days.push(d.toISOString().split("T")[0]);
  }
  return days;
}

function formatDayLabel(key: string): string {
  const d = new Date(key + "T12:00:00");
  const weekday = d.toLocaleDateString("en", { weekday: "short" });
  const monthDay = d.toLocaleDateString("en", { month: "short", day: "numeric" });
  const city = cityForDate(key);
  const cityLabel = CITY_LABEL[city] ?? city;
  return `${weekday} ${monthDay} (${cityLabel})`;
}

const CATEGORY_ICONS: Record<string, string> = {
  shrine: "⛩️",
  temple: "🕌",
  food: "🍜",
  restaurant: "🍱",
  market: "🛒",
  shopping: "🛍️",
  park: "🌳",
  museum: "🏛️",
  landmark: "🗺️",
  onsen: "♨️",
  transport: "🚆",
  hotel: "🏨",
  entertainment: "🎭",
  nature: "🌿",
  castle: "🏯",
};

function categoryIcon(category: string | null): string {
  if (!category) return "📍";
  const key = category.toLowerCase();
  for (const [k, v] of Object.entries(CATEGORY_ICONS)) {
    if (key.includes(k)) return v;
  }
  return "📍";
}

interface ScheduleModalProps {
  poi: Poi;
  onClose: () => void;
  onScheduled: () => void;
}

function ScheduleModal({ poi, onClose, onScheduled }: ScheduleModalProps) {
  const days = tripDays();
  const [selectedDate, setSelectedDate] = useState(days[0]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await api.planning.schedule({
        date: selectedDate,
        poi_name: poi.name_en,
        city: poi.city ?? cityForDate(selectedDate),
        notes: "",
      });
      setSuccess(true);
      setTimeout(() => {
        onScheduled();
        onClose();
      }, 1200);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to schedule — backend may not be ready yet.";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)",
      display: "flex", alignItems: "center", justifyContent: "center",
      zIndex: 1000, padding: "1rem",
    }}
      onClick={onClose}
    >
      <div
        style={{
          background: "white", borderRadius: "16px", padding: "1.5rem",
          maxWidth: "420px", width: "100%", boxShadow: "0 20px 60px rgba(0,0,0,0.2)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ fontWeight: 700, marginBottom: "0.25rem", fontSize: "1rem" }}>
          📅 Schedule POI
        </h3>
        <p style={{ fontSize: "0.85rem", color: "#6b7280", marginBottom: "1rem" }}>
          {poi.name_en}{poi.name_ja ? ` · ${poi.name_ja}` : ""}
        </p>

        <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.4rem", color: "#374151" }}>
          Select trip date
        </label>
        <select
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          style={{
            width: "100%", padding: "0.6rem 0.75rem", borderRadius: "8px",
            border: "1.5px solid #d1d5db", fontSize: "0.875rem",
            background: "white", marginBottom: "1rem", color: "#111827",
          }}
        >
          {days.map((d) => (
            <option key={d} value={d}>{formatDayLabel(d)}</option>
          ))}
        </select>

        {error && (
          <div style={{ fontSize: "0.8rem", color: "#dc2626", background: "#fee2e2", borderRadius: "8px", padding: "0.5rem 0.75rem", marginBottom: "0.75rem" }}>
            {error}
          </div>
        )}
        {success && (
          <div style={{ fontSize: "0.8rem", color: "#16a34a", background: "#dcfce7", borderRadius: "8px", padding: "0.5rem 0.75rem", marginBottom: "0.75rem" }}>
            Scheduled successfully!
          </div>
        )}

        <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end" }}>
          <button
            onClick={onClose}
            style={{
              padding: "0.5rem 1rem", borderRadius: "8px", border: "1.5px solid #d1d5db",
              background: "white", color: "#374151", cursor: "pointer", fontSize: "0.875rem",
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting}
            style={{
              padding: "0.5rem 1.25rem", borderRadius: "8px", border: "none",
              background: submitting ? "#94a3b8" : "#1d4ed8", color: "white",
              cursor: submitting ? "not-allowed" : "pointer", fontWeight: 600,
              fontSize: "0.875rem",
            }}
          >
            {submitting ? "Scheduling…" : "Confirm"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function PlanningPage() {
  const days = tripDays();
  const [mapOpen, setMapOpen] = useState(false);

  const [pois, setPois] = useState<Poi[]>([]);
  // Itinerary keyed by date string → array of legs/items
  const [itinerary, setItinerary] = useState<Record<string, unknown[]>>({});
  const [loadingPois, setLoadingPois] = useState(true);
  const [loadingItinerary, setLoadingItinerary] = useState(true);
  const [modalPoi, setModalPoi] = useState<Poi | null>(null);
  const [poiFilter, setPoiFilter] = useState<string>("all");

  useEffect(() => {
    (api.pois.list() as Promise<Poi[]>)
      .then((d) => setPois(d))
      .catch(() => setPois([]))
      .finally(() => setLoadingPois(false));
  }, []);

  const fetchItinerary = useCallback(async () => {
    setLoadingItinerary(true);
    try {
      const legs = await (api.itinerary.list() as Promise<ItineraryLeg[]>);
      const grouped: Record<string, unknown[]> = {};
      for (const leg of legs) {
        if (leg.date_start) {
          if (!grouped[leg.date_start]) grouped[leg.date_start] = [];
          grouped[leg.date_start].push(leg);
        }
      }
      setItinerary(grouped);
    } catch {
      setItinerary({});
    } finally {
      setLoadingItinerary(false);
    }
  }, []);

  useEffect(() => {
    fetchItinerary();
  }, [fetchItinerary]);

  // Unique city values for filter
  const cityOptions = Array.from(new Set(pois.map((p) => p.city).filter(Boolean))) as string[];

  const filteredPois = poiFilter === "all" ? pois : pois.filter((p) => p.city === poiFilter);

  // Group POIs by city for the browser panel
  const poisByCity: Record<string, Poi[]> = {};
  for (const poi of filteredPois) {
    const city = poi.city ?? "other";
    if (!poisByCity[city]) poisByCity[city] = [];
    poisByCity[city].push(poi);
  }

  return (
    <div style={{ padding: "1.5rem", maxWidth: "1400px" }}>
      <h1 style={{ fontWeight: 800, fontSize: "1.5rem", marginBottom: "0.25rem" }}>
        📋 Trip Planning
      </h1>
      <p style={{ color: "#6b7280", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
        Browse POIs and schedule them onto your trip timeline · Mar 23 – Apr 9, 2026
      </p>

      {/* Collapsible trip map */}
      <div style={{ marginBottom: "1.5rem", background: "white", borderRadius: "14px", boxShadow: "0 1px 4px rgba(0,0,0,0.08)", overflow: "hidden" }}>
        <button
          onClick={() => setMapOpen((v) => !v)}
          style={{
            width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: "0.875rem 1rem", background: "none", border: "none", cursor: "pointer",
            textAlign: "left",
          }}
        >
          <span style={{ fontWeight: 700, fontSize: "0.95rem" }}>🗺️ Trip Map</span>
          <span style={{ fontSize: "0.8rem", color: "#6b7280" }}>
            {mapOpen ? "▲ Collapse" : "▼ Expand"}
          </span>
        </button>
        {mapOpen && (
          <div style={{ padding: "0 1rem 1rem" }}>
            <TripMap height="450px" />
          </div>
        )}
      </div>

      <div style={{
        display: "grid",
        gridTemplateColumns: "40% 1fr",
        gap: "1.5rem",
        alignItems: "start",
      }}
        className="planning-grid"
      >
        {/* Left panel: POI browser */}
        <div style={{ position: "sticky", top: "1rem", maxHeight: "calc(100vh - 6rem)", overflowY: "auto" }}>
          <div style={{
            background: "white", borderRadius: "14px",
            boxShadow: "0 1px 4px rgba(0,0,0,0.08)", overflow: "hidden",
          }}>
            <div style={{ padding: "1rem 1rem 0.75rem", borderBottom: "1px solid #f1f5f9" }}>
              <div style={{ fontWeight: 700, fontSize: "0.95rem", marginBottom: "0.6rem" }}>
                📍 POI Browser
              </div>
              <select
                value={poiFilter}
                onChange={(e) => setPoiFilter(e.target.value)}
                style={{
                  width: "100%", padding: "0.45rem 0.65rem", borderRadius: "7px",
                  border: "1.5px solid #e5e7eb", fontSize: "0.8rem",
                  background: "white", color: "#374151",
                }}
              >
                <option value="all">All cities</option>
                {cityOptions.map((c) => (
                  <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                ))}
              </select>
            </div>

            {loadingPois ? (
              <div style={{ padding: "2rem", textAlign: "center", color: "#94a3b8", fontSize: "0.85rem" }}>
                Loading POIs…
              </div>
            ) : pois.length === 0 ? (
              <div style={{ padding: "2rem", textAlign: "center", color: "#94a3b8", fontSize: "0.85rem" }}>
                No POIs found
              </div>
            ) : (
              <div style={{ padding: "0.75rem" }}>
                {Object.entries(poisByCity).map(([city, cityPois]) => (
                  <div key={city} style={{ marginBottom: "1rem" }}>
                    <div style={{
                      fontSize: "0.7rem", fontWeight: 700, textTransform: "uppercase",
                      letterSpacing: "0.07em", color: CITY_BADGE_COLOR[city] ?? "#6b7280",
                      marginBottom: "0.4rem", paddingLeft: "0.25rem",
                    }}>
                      {CITY_LABEL[city] ?? city}
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                      {cityPois.map((poi) => (
                        <div key={poi.id} style={{
                          display: "flex", alignItems: "center", gap: "0.6rem",
                          padding: "0.6rem 0.75rem", background: CITY_BG[city] ?? "#f8fafc",
                          borderRadius: "9px", border: "1px solid rgba(0,0,0,0.05)",
                        }}>
                          <span style={{ fontSize: "1.1rem", flexShrink: 0 }}>
                            {categoryIcon(poi.category)}
                          </span>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ fontWeight: 600, fontSize: "0.8rem", lineHeight: "1.2", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                              {poi.name_en}
                            </div>
                            {poi.category && (
                              <div style={{ fontSize: "0.68rem", color: "#9ca3af", marginTop: "1px" }}>
                                {poi.category}
                              </div>
                            )}
                          </div>
                          <button
                            onClick={() => setModalPoi(poi)}
                            style={{
                              flexShrink: 0, padding: "0.3rem 0.6rem",
                              background: "#1d4ed8", color: "white", border: "none",
                              borderRadius: "6px", cursor: "pointer", fontSize: "0.7rem",
                              fontWeight: 600, whiteSpace: "nowrap",
                            }}
                          >
                            📅 Schedule
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right panel: Trip timeline */}
        <div>
          <div style={{ fontWeight: 700, fontSize: "0.95rem", marginBottom: "0.75rem" }}>
            🗓️ Trip Timeline
          </div>
          {loadingItinerary && (
            <div style={{ color: "#94a3b8", fontSize: "0.85rem", marginBottom: "0.75rem" }}>
              Loading itinerary…
            </div>
          )}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
            {days.map((dateKey) => {
              const city = cityForDate(dateKey);
              const dayLegs = (itinerary[dateKey] ?? []) as Array<{ title?: string; name?: string; trip_poi_id?: number | null }>;
              const d = new Date(dateKey + "T12:00:00");
              const weekday = d.toLocaleDateString("en", { weekday: "short" });
              const monthDay = d.toLocaleDateString("en", { month: "short", day: "numeric" });

              return (
                <div key={dateKey} style={{
                  background: CITY_BG[city] ?? "white",
                  borderRadius: "10px",
                  padding: "0.75rem 1rem",
                  border: "1px solid rgba(0,0,0,0.06)",
                  boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.4rem" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                      <span style={{ fontWeight: 700, fontSize: "0.875rem" }}>
                        {weekday} {monthDay}
                      </span>
                      <span style={{
                        fontSize: "0.65rem", fontWeight: 700, padding: "2px 8px",
                        borderRadius: "9999px", color: "white",
                        background: CITY_BADGE_COLOR[city] ?? "#6b7280",
                      }}>
                        {CITY_LABEL[city] ?? city}
                      </span>
                    </div>
                    <button
                      onClick={() => {
                        // Open modal without pre-selecting a POI — let user pick from filter
                        // For "+" quick-add, show modal with first POI for this city or any
                        const cityPois = pois.filter((p) => p.city === city);
                        const target = cityPois[0] ?? pois[0];
                        if (target) setModalPoi(target);
                      }}
                      style={{
                        width: "24px", height: "24px", borderRadius: "50%",
                        background: "#e5e7eb", border: "none", cursor: "pointer",
                        fontSize: "1rem", lineHeight: "1", display: "flex",
                        alignItems: "center", justifyContent: "center",
                        color: "#374151", fontWeight: 700,
                      }}
                      title="Add POI to this day"
                    >
                      +
                    </button>
                  </div>

                  {dayLegs.length > 0 ? (
                    <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "0.2rem" }}>
                      {dayLegs.map((leg, i) => (
                        <li key={i} style={{ fontSize: "0.78rem", color: "#374151", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                          <span style={{ color: "#9ca3af", fontSize: "0.7rem" }}>▸</span>
                          {leg.trip_poi_id ? (
                            <Link href={`/pois/${leg.trip_poi_id}`} style={{ color: "var(--city-accent, #1d4ed8)", textDecoration: "none" }}>
                              {leg.title ?? "Unnamed item"}
                            </Link>
                          ) : (
                            leg.title ?? "Unnamed item"
                          )}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div style={{ fontSize: "0.72rem", color: "#9ca3af", fontStyle: "italic" }}>
                      No legs scheduled yet
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Schedule modal */}
      {modalPoi && (
        <ScheduleModal
          poi={modalPoi}
          onClose={() => setModalPoi(null)}
          onScheduled={fetchItinerary}
        />
      )}

      <style>{`
        @media (max-width: 900px) {
          .planning-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
}
