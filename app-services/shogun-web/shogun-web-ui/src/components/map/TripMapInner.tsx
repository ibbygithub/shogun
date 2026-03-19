"use client";

import { useState, useEffect, useRef } from "react";
import {
  APIProvider,
  Map,
  AdvancedMarker,
  useMap,
} from "@vis.gl/react-google-maps";
import type { ItineraryLeg, Poi } from "@/lib/types";
import { api } from "@/lib/api";

// ── City focus positions ───────────────────────────────────────────────────────
const CITY_FOCUS = {
  all:      { lat: 36.2,    lng: 138.5,   zoom: 6  },
  osaka:    { lat: 34.6937, lng: 135.5023, zoom: 13 },
  kanazawa: { lat: 36.5611, lng: 136.6561, zoom: 13 },
  tokyo:    { lat: 35.6762, lng: 139.6503, zoom: 12 },
};

// ── Leg type → colour mapping ──────────────────────────────────────────────────
type PinStyle = { bg: string; border: string; emoji: string };

const TYPE_COLORS: Record<string, PinStyle> = {
  accommodation: { bg: "#FFD700", border: "#B8860B", emoji: "🏠" },
  restaurant:    { bg: "#16a34a", border: "#15803d", emoji: "🍽️" },
  eat:           { bg: "#16a34a", border: "#15803d", emoji: "🍜" },
  food:          { bg: "#16a34a", border: "#15803d", emoji: "🍱" },
  dining:        { bg: "#16a34a", border: "#15803d", emoji: "🍱" },
  attraction:    { bg: "#2563eb", border: "#1d4ed8", emoji: "🏛️" },
  sightseeing:   { bg: "#2563eb", border: "#1d4ed8", emoji: "🗺️" },
  destination:   { bg: "#2563eb", border: "#1d4ed8", emoji: "📍" },
  visit:         { bg: "#2563eb", border: "#1d4ed8", emoji: "🏯" },
  activity:      { bg: "#f97316", border: "#ea580c", emoji: "🎭" },
  entertainment: { bg: "#f97316", border: "#ea580c", emoji: "🎌" },
  transit:       { bg: "#dc2626", border: "#b91c1c", emoji: "🚆" },
  transport:     { bg: "#dc2626", border: "#b91c1c", emoji: "🚌" },
  travel:        { bg: "#dc2626", border: "#b91c1c", emoji: "✈️" },
  flight:        { bg: "#dc2626", border: "#b91c1c", emoji: "✈️" },
  train:         { bg: "#dc2626", border: "#b91c1c", emoji: "🚄" },
};

const DEFAULT_PIN: PinStyle = { bg: "#6b7280", border: "#4b5563", emoji: "📍" };
const POI_PIN:     PinStyle = { bg: "#9333ea", border: "#7e22ce", emoji: "✨" };
const ACC_PIN:     PinStyle = { bg: "#FFD700", border: "#B8860B", emoji: "🏠" };

function getLegPin(legType: string | null): PinStyle {
  if (!legType) return DEFAULT_PIN;
  const key = legType.toLowerCase();
  for (const [k, v] of Object.entries(TYPE_COLORS)) {
    if (key.includes(k)) return v;
  }
  return DEFAULT_PIN;
}

// ── Geocoding helper ───────────────────────────────────────────────────────────
interface LatLng { lat: number; lng: number }

async function geocode(address: string, apiKey: string): Promise<LatLng | null> {
  const cacheKey = `geocode:${address}`;
  try {
    const cached = sessionStorage.getItem(cacheKey);
    if (cached) return JSON.parse(cached) as LatLng;
  } catch { /* sessionStorage unavailable */ }

  try {
    const url = `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(address)}&key=${encodeURIComponent(apiKey)}`;
    const res = await fetch(url);
    const data = await res.json();
    if (data.status === "OK" && data.results?.length > 0) {
      const loc = data.results[0].geometry.location as LatLng;
      try { sessionStorage.setItem(cacheKey, JSON.stringify(loc)); } catch { /* ok */ }
      return loc;
    }
  } catch { /* network error */ }
  return null;
}

// ── MapCameraController — must live inside <Map> ───────────────────────────────
interface CameraTarget extends LatLng { zoom: number }

function MapCameraController({
  target,
  onDone,
}: {
  target: CameraTarget | null;
  onDone: () => void;
}) {
  const map = useMap();
  const prevTarget = useRef<CameraTarget | null>(null);

  useEffect(() => {
    if (!map || !target) return;
    if (prevTarget.current === target) return;
    prevTarget.current = target;
    map.panTo({ lat: target.lat, lng: target.lng });
    map.setZoom(target.zoom);
    onDone();
  }, [map, target, onDone]);

  return null;
}

// ── Custom marker pin ──────────────────────────────────────────────────────────
function MarkerPin({
  pin,
  hovered,
  selected,
  label,
  notes,
  onEnter,
  onLeave,
}: {
  pin: PinStyle;
  hovered: boolean;
  selected: boolean;
  label: string;
  notes?: string | null;
  onEnter: () => void;
  onLeave: () => void;
}) {
  return (
    <div
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      style={{ position: "relative", cursor: "pointer" }}
    >
      {/* Tooltip on hover */}
      {hovered && (
        <div
          style={{
            position: "absolute",
            bottom: "calc(100% + 10px)",
            left: "50%",
            transform: "translateX(-50%)",
            background: "rgba(15,23,42,0.92)",
            color: "white",
            borderRadius: "8px",
            padding: "6px 10px",
            fontSize: "11px",
            whiteSpace: "nowrap",
            maxWidth: "220px",
            overflow: "hidden",
            textOverflow: "ellipsis",
            pointerEvents: "none",
            zIndex: 1000,
            boxShadow: "0 4px 12px rgba(0,0,0,0.35)",
            lineHeight: "1.4",
          }}
        >
          <div style={{ fontWeight: 700, whiteSpace: "normal", maxWidth: "200px" }}>{label}</div>
          {notes && (
            <div style={{ color: "#94a3b8", fontSize: "10px", marginTop: "2px", whiteSpace: "normal" }}>
              {notes.length > 80 ? notes.slice(0, 80) + "…" : notes}
            </div>
          )}
        </div>
      )}

      {/* Pin circle */}
      <div
        style={{
          width: selected ? 26 : 22,
          height: selected ? 26 : 22,
          borderRadius: "50%",
          background: pin.bg,
          border: `3px solid ${pin.border}`,
          boxShadow: selected
            ? `0 0 0 3px ${pin.bg}55, 0 4px 12px rgba(0,0,0,0.4)`
            : "0 2px 6px rgba(0,0,0,0.35)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: selected ? "12px" : "10px",
          transform: selected ? "scale(1.15)" : hovered ? "scale(1.1)" : "scale(1)",
          transition: "transform 0.12s, box-shadow 0.12s, width 0.12s, height 0.12s",
        }}
      >
        {pin.emoji}
      </div>
    </div>
  );
}

// ── Side panel ─────────────────────────────────────────────────────────────────
function LegTypeChip({ type }: { type: string | null }) {
  const pin = getLegPin(type);
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
        padding: "2px 10px",
        borderRadius: "999px",
        background: pin.bg + "22",
        color: pin.border,
        fontWeight: 700,
        fontSize: "0.72rem",
        border: `1.5px solid ${pin.bg}`,
        textTransform: "capitalize",
      }}
    >
      {pin.emoji} {type ?? "other"}
    </span>
  );
}

interface SidePanelProps {
  leg: ItineraryLeg | null;
  poi: Poi | null;
  accLabel: string | null;
  onClose: () => void;
}

function SidePanel({ leg, poi, accLabel, onClose }: SidePanelProps) {
  if (!leg && !poi && !accLabel) return null;

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        right: 0,
        width: "300px",
        height: "100%",
        background: "white",
        boxShadow: "-4px 0 24px rgba(0,0,0,0.16)",
        zIndex: 30,
        display: "flex",
        flexDirection: "column",
        borderRadius: "0 0 0 0",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "0.875rem 1rem",
          borderBottom: "1px solid #f1f5f9",
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: "0.5rem",
          background: "#fafafa",
        }}
      >
        <div style={{ flex: 1 }}>
          {leg && <LegTypeChip type={leg.leg_type} />}
          {poi && (
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                padding: "2px 10px",
                borderRadius: "999px",
                background: "#9333ea22",
                color: "#7e22ce",
                fontWeight: 700,
                fontSize: "0.72rem",
                border: "1.5px solid #9333ea",
              }}
            >
              ✨ POI Suggestion
            </span>
          )}
          {accLabel && (
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                padding: "2px 10px",
                borderRadius: "999px",
                background: "#FFD70022",
                color: "#B8860B",
                fontWeight: 700,
                fontSize: "0.72rem",
                border: "1.5px solid #FFD700",
              }}
            >
              🏠 Accommodation
            </span>
          )}
        </div>
        <button
          onClick={onClose}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            fontSize: "1rem",
            color: "#9ca3af",
            padding: "2px",
            lineHeight: 1,
            flexShrink: 0,
          }}
        >
          ✕
        </button>
      </div>

      {/* Body */}
      <div style={{ padding: "1rem", overflowY: "auto", flex: 1 }}>
        {/* Itinerary leg */}
        {leg && (
          <>
            <h3 style={{ fontWeight: 800, fontSize: "1rem", marginBottom: "0.75rem", lineHeight: 1.3 }}>
              {leg.title}
            </h3>

            {leg.city && (
              <Row label="City">
                <span style={{ textTransform: "capitalize" }}>{leg.city}</span>
              </Row>
            )}

            {(leg.date_start || leg.date_end) && (
              <Row label="Date">
                {leg.date_start ?? ""}
                {leg.date_end && leg.date_end !== leg.date_start ? ` → ${leg.date_end}` : ""}
              </Row>
            )}

            {leg.address_en && <Row label="Address">{leg.address_en}</Row>}
            {leg.address_ja && <Row label="住所">{leg.address_ja}</Row>}
            {leg.confirmation_number && (
              <Row label="Confirmation">
                <code style={{ fontSize: "0.8rem", background: "#f1f5f9", padding: "1px 5px", borderRadius: "4px" }}>
                  {leg.confirmation_number}
                </code>
              </Row>
            )}

            {leg.description && (
              <div style={{ marginTop: "0.75rem" }}>
                <div style={{ fontSize: "0.7rem", fontWeight: 700, textTransform: "uppercase", color: "#94a3b8", letterSpacing: "0.06em", marginBottom: "0.3rem" }}>
                  Description
                </div>
                <p style={{ fontSize: "0.83rem", color: "#374151", lineHeight: 1.5, margin: 0 }}>
                  {leg.description}
                </p>
              </div>
            )}

            {leg.notes && (
              <div style={{ marginTop: "0.75rem", background: "#fef9c3", borderRadius: "8px", padding: "0.6rem 0.75rem", border: "1px solid #fde047" }}>
                <div style={{ fontSize: "0.7rem", fontWeight: 700, color: "#a16207", marginBottom: "0.25rem" }}>
                  📝 Notes
                </div>
                <p style={{ fontSize: "0.8rem", color: "#713f12", lineHeight: 1.5, margin: 0 }}>
                  {leg.notes}
                </p>
              </div>
            )}

            {leg.status && leg.status !== "confirmed" && (
              <Row label="Status">
                <span style={{ textTransform: "capitalize", color: "#f97316", fontWeight: 600 }}>
                  {leg.status}
                </span>
              </Row>
            )}
          </>
        )}

        {/* Accommodation */}
        {accLabel && !leg && (
          <>
            <h3 style={{ fontWeight: 800, fontSize: "1rem", marginBottom: "0.75rem" }}>
              {accLabel}
            </h3>
            <p style={{ fontSize: "0.83rem", color: "#6b7280" }}>
              Your accommodation for this city.
            </p>
          </>
        )}

        {/* POI suggestion */}
        {poi && (
          <>
            <h3 style={{ fontWeight: 800, fontSize: "1rem", marginBottom: "0.75rem", lineHeight: 1.3 }}>
              {poi.name_en}
              {poi.name_ja && (
                <span style={{ display: "block", fontWeight: 500, fontSize: "0.82rem", color: "#9ca3af", marginTop: "2px" }}>
                  {poi.name_ja}
                </span>
              )}
            </h3>

            {poi.category && <Row label="Category">{poi.category}</Row>}
            {poi.city && <Row label="City"><span style={{ textTransform: "capitalize" }}>{poi.city}</span></Row>}
            {poi.best_time && <Row label="Best time">{poi.best_time}</Row>}

            {poi.description && (
              <div style={{ marginTop: "0.75rem" }}>
                <div style={{ fontSize: "0.7rem", fontWeight: 700, textTransform: "uppercase", color: "#94a3b8", letterSpacing: "0.06em", marginBottom: "0.3rem" }}>
                  About
                </div>
                <p style={{ fontSize: "0.83rem", color: "#374151", lineHeight: 1.5, margin: 0 }}>
                  {poi.description}
                </p>
              </div>
            )}

            {poi.crowd_notes && (
              <div style={{ marginTop: "0.75rem", background: "#eff6ff", borderRadius: "8px", padding: "0.6rem 0.75rem", border: "1px solid #bfdbfe" }}>
                <div style={{ fontSize: "0.7rem", fontWeight: 700, color: "#1d4ed8", marginBottom: "0.25rem" }}>
                  👥 Crowd Tips
                </div>
                <p style={{ fontSize: "0.8rem", color: "#1e3a8a", lineHeight: 1.5, margin: 0 }}>
                  {poi.crowd_notes}
                </p>
              </div>
            )}

            {poi.map_url && (
              <a
                href={poi.map_url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: "inline-block",
                  marginTop: "1rem",
                  padding: "0.4rem 0.9rem",
                  background: "#1d4ed8",
                  color: "white",
                  borderRadius: "8px",
                  fontSize: "0.78rem",
                  fontWeight: 600,
                  textDecoration: "none",
                }}
              >
                🗺️ Open in Maps
              </a>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.4rem", fontSize: "0.8rem" }}>
      <span style={{ color: "#9ca3af", minWidth: "90px", fontWeight: 600, fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.04em", paddingTop: "1px" }}>
        {label}
      </span>
      <span style={{ color: "#374151", flex: 1 }}>{children}</span>
    </div>
  );
}

// ── Legend ─────────────────────────────────────────────────────────────────────
function Legend({ showKb }: { showKb: boolean }) {
  const items: [string, string, string][] = [
    ["#FFD700", "#B8860B", "Accommodation"],
    ["#16a34a", "#15803d", "Restaurant"],
    ["#2563eb", "#1d4ed8", "Attraction"],
    ["#f97316", "#ea580c", "Activity"],
    ["#dc2626", "#b91c1c", "Transit"],
  ];
  if (showKb) items.push(["#9333ea", "#7e22ce", "POI Suggestions"]);

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "8px 14px",
        padding: "6px 10px",
        background: "rgba(255,255,255,0.92)",
        borderRadius: "8px",
        backdropFilter: "blur(4px)",
        boxShadow: "0 1px 6px rgba(0,0,0,0.1)",
      }}
    >
      {items.map(([bg, border, label]) => (
        <div key={label} style={{ display: "flex", alignItems: "center", gap: "5px" }}>
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: "50%",
              background: bg,
              border: `2px solid ${border}`,
              flexShrink: 0,
            }}
          />
          <span style={{ fontSize: "11px", color: "#374151", whiteSpace: "nowrap" }}>{label}</span>
        </div>
      ))}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────
interface TripMapInnerProps {
  height?: string;
}

export default function TripMapInner({ height = "600px" }: TripMapInnerProps) {
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ?? "";

  const [legs, setLegs] = useState<ItineraryLeg[]>([]);
  const [pois, setPois] = useState<Poi[]>([]);
  const [geocoded, setGeocoded] = useState<Record<number, LatLng>>({});
  const [geocodingDone, setGeocodingDone] = useState(false);
  const [showKbLayer, setShowKbLayer] = useState(false);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [selectedLeg, setSelectedLeg] = useState<ItineraryLeg | null>(null);
  const [selectedPoi, setSelectedPoi] = useState<Poi | null>(null);
  const [cameraTarget, setCameraTarget] = useState<CameraTarget | null>(null);
  const [activeCity, setActiveCity] = useState<"all" | "osaka" | "kanazawa" | "tokyo">("all");

  // Load data
  useEffect(() => {
    (api.itinerary.list() as Promise<ItineraryLeg[]>)
      .then((d) => setLegs(d))
      .catch(() => setLegs([]));

    (api.pois.list() as Promise<Poi[]>)
      .then((d) => setPois(d))
      .catch(() => setPois([]));
  }, []);

  // Geocode legs after they load
  useEffect(() => {
    if (legs.length === 0 || !apiKey) {
      setGeocodingDone(true);
      return;
    }

    const legsToGeocode = legs.filter(
      (l) => l.address_en || l.address_ja
    );

    if (legsToGeocode.length === 0) {
      setGeocodingDone(true);
      return;
    }

    Promise.all(
      legsToGeocode.map(async (leg) => {
        const address = leg.address_en ?? leg.address_ja ?? "";
        const coords = await geocode(address, apiKey);
        return { id: leg.id, coords };
      })
    ).then((results) => {
      const map: Record<number, LatLng> = {};
      for (const { id, coords } of results) {
        if (coords) map[id] = coords;
      }
      setGeocoded(map);
      setGeocodingDone(true);
    });
  }, [legs, apiKey]);

  const focusCity = (city: "all" | "osaka" | "kanazawa" | "tokyo") => {
    setActiveCity(city);
    setCameraTarget(CITY_FOCUS[city]);
  };

  const handleLegClick = (leg: ItineraryLeg, coords: LatLng) => {
    setSelectedLeg(leg);
    setSelectedPoi(null);
    setSelectedAcc(null);
    setCameraTarget({ ...coords, zoom: 16 });
  };

  const handlePoiClick = (poi: Poi) => {
    if (!poi.lat || !poi.lng) return;
    setSelectedPoi(poi);
    setSelectedLeg(null);
    setCameraTarget({ lat: poi.lat, lng: poi.lng, zoom: 16 });
  };

  const closePanel = () => {
    setSelectedLeg(null);
    setSelectedPoi(null);
  };

  const panelOpen = !!(selectedLeg || selectedPoi);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      {/* Controls row */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "8px",
        }}
      >
        {/* City focus buttons */}
        <div style={{ display: "flex", gap: "6px" }}>
          {(["osaka", "kanazawa", "tokyo", "all"] as const).map((city) => {
            const labels: Record<string, string> = {
              osaka: "🏯 Osaka",
              kanazawa: "🌸 Kanazawa",
              tokyo: "🗼 Tokyo",
              all: "🗾 All Japan",
            };
            const active = activeCity === city;
            return (
              <button
                key={city}
                onClick={() => focusCity(city)}
                style={{
                  padding: "5px 12px",
                  borderRadius: "999px",
                  border: active ? "2px solid #1d4ed8" : "1.5px solid #e5e7eb",
                  background: active ? "#1d4ed8" : "white",
                  color: active ? "white" : "#374151",
                  fontWeight: active ? 700 : 500,
                  fontSize: "0.78rem",
                  cursor: "pointer",
                  transition: "all 0.15s",
                }}
              >
                {labels[city]}
              </button>
            );
          })}
        </div>

        {/* Divider */}
        <div style={{ width: "1px", height: "24px", background: "#e5e7eb", margin: "0 2px" }} />

        {/* KB toggle */}
        <button
          onClick={() => setShowKbLayer((v) => !v)}
          style={{
            padding: "5px 12px",
            borderRadius: "999px",
            border: showKbLayer ? "2px solid #9333ea" : "1.5px solid #e5e7eb",
            background: showKbLayer ? "#9333ea" : "white",
            color: showKbLayer ? "white" : "#7e22ce",
            fontWeight: 600,
            fontSize: "0.78rem",
            cursor: "pointer",
            transition: "all 0.15s",
          }}
        >
          ✨ {showKbLayer ? "Hide" : "Show"} POI Suggestions
        </button>

        {!geocodingDone && (
          <span style={{ fontSize: "0.75rem", color: "#9ca3af" }}>Geocoding…</span>
        )}
      </div>

      {/* Legend */}
      <Legend showKb={showKbLayer} />

      {/* Map container */}
      <div style={{ position: "relative", width: "100%", height, borderRadius: "12px", overflow: "hidden", boxShadow: "0 2px 16px rgba(0,0,0,0.12)" }}>
        {!apiKey ? (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", background: "#f1f5f9", color: "#9ca3af", fontSize: "0.9rem" }}>
            Google Maps API key not configured (NEXT_PUBLIC_GOOGLE_MAPS_API_KEY)
          </div>
        ) : (
          <APIProvider apiKey={apiKey}>
            <Map
              defaultCenter={CITY_FOCUS.all}
              defaultZoom={CITY_FOCUS.all.zoom}
              mapId="DEMO_MAP_ID"
              style={{ width: "100%", height: "100%" }}
              gestureHandling="greedy"
              disableDefaultUI={false}
              onClick={panelOpen ? closePanel : undefined}
            >
              <MapCameraController
                target={cameraTarget}
                onDone={() => setCameraTarget(null)}
              />

              {/* Itinerary leg markers (geocoded from address_en/address_ja) */}
              {legs.map((leg) => {
                const coords = geocoded[leg.id];
                if (!coords) return null;
                const pinId = `leg-${leg.id}`;
                const isHov = hoveredId === pinId;
                const isSel = selectedLeg?.id === leg.id;
                const pin = getLegPin(leg.leg_type);
                return (
                  <AdvancedMarker
                    key={pinId}
                    position={coords}
                    onClick={() => handleLegClick(leg, coords)}
                    zIndex={isSel ? 100 : 5}
                  >
                    <MarkerPin
                      pin={pin}
                      hovered={isHov}
                      selected={isSel}
                      label={leg.title}
                      notes={leg.notes}
                      onEnter={() => setHoveredId(pinId)}
                      onLeave={() => setHoveredId(null)}
                    />
                  </AdvancedMarker>
                );
              })}

              {/* Knowledge base POI suggestion layer (toggleable, purple) */}
              {showKbLayer &&
                pois
                  .filter(
                    (p): p is Poi & { lat: number; lng: number } =>
                      typeof p.lat === "number" && typeof p.lng === "number"
                  )
                  .map((poi) => {
                    const pinId = `poi-${poi.id}`;
                    const isHov = hoveredId === pinId;
                    const isSel = selectedPoi?.id === poi.id;
                    return (
                      <AdvancedMarker
                        key={pinId}
                        position={{ lat: poi.lat, lng: poi.lng }}
                        onClick={() => handlePoiClick(poi)}
                        zIndex={isSel ? 100 : 3}
                      >
                        <MarkerPin
                          pin={POI_PIN}
                          hovered={isHov}
                          selected={isSel}
                          label={poi.name_en}
                          notes={poi.crowd_notes ?? poi.description}
                          onEnter={() => setHoveredId(pinId)}
                          onLeave={() => setHoveredId(null)}
                        />
                      </AdvancedMarker>
                    );
                  })}
            </Map>
          </APIProvider>
        )}

        {/* Side panel — overlays on the right of the map */}
        <SidePanel
          leg={selectedLeg}
          poi={selectedPoi}
          accLabel={null}
          onClose={closePanel}
        />
      </div>
    </div>
  );
}
