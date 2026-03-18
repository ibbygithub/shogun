"use client";

import { useState, useEffect, useRef } from "react";
import {
  APIProvider,
  Map,
  AdvancedMarker,
  InfoWindow,
  useMap,
} from "@vis.gl/react-google-maps";
import type { Poi } from "@/lib/types";

// ── Hardcoded accommodation coordinates (matches TripMapInner) ─────────────────
const ACCOMMODATIONS: Record<string, { lat: number; lng: number; label: string }> = {
  osaka:    { lat: 34.7255, lng: 135.5185, label: "Tenjinbashi Queen Airbnb" },
  kanazawa: { lat: 36.5613, lng: 136.6562, label: "Hotel Sanraku Kanazawa" },
  tokyo:    { lat: 35.7358, lng: 139.7283, label: "Sugamo Airbnb" },
  nara:     { lat: 34.6851, lng: 135.8048, label: "Nara Park (day trip)" },
};

// ── Category → pin colour mapping ─────────────────────────────────────────────
interface PinStyle { bg: string; border: string; emoji: string }

const CATEGORY_PINS: Record<string, PinStyle> = {
  shrine:        { bg: "#8b5cf6", border: "#7c3aed", emoji: "⛩️" },
  temple:        { bg: "#8b5cf6", border: "#7c3aed", emoji: "🕌" },
  food:          { bg: "#16a34a", border: "#15803d", emoji: "🍜" },
  restaurant:    { bg: "#16a34a", border: "#15803d", emoji: "🍱" },
  market:        { bg: "#d97706", border: "#b45309", emoji: "🛒" },
  shopping:      { bg: "#d97706", border: "#b45309", emoji: "🛍️" },
  vintage:       { bg: "#d97706", border: "#b45309", emoji: "👘" },
  park:          { bg: "#059669", border: "#047857", emoji: "🌳" },
  nature:        { bg: "#059669", border: "#047857", emoji: "🌿" },
  garden:        { bg: "#059669", border: "#047857", emoji: "🌸" },
  museum:        { bg: "#2563eb", border: "#1d4ed8", emoji: "🏛️" },
  landmark:      { bg: "#2563eb", border: "#1d4ed8", emoji: "🗺️" },
  castle:        { bg: "#2563eb", border: "#1d4ed8", emoji: "🏯" },
  art:           { bg: "#2563eb", border: "#1d4ed8", emoji: "🎨" },
  onsen:         { bg: "#dc2626", border: "#b91c1c", emoji: "♨️" },
  entertainment: { bg: "#f97316", border: "#ea580c", emoji: "🎭" },
  amusement:     { bg: "#f97316", border: "#ea580c", emoji: "🎡" },
  hotel:         { bg: "#FFD700", border: "#B8860B", emoji: "🏨" },
  skincare:      { bg: "#ec4899", border: "#db2777", emoji: "🧴" },
  pharmacy:      { bg: "#ec4899", border: "#db2777", emoji: "💊" },
  sake:          { bg: "#a16207", border: "#854d0e", emoji: "🍶" },
  knife:         { bg: "#6b7280", border: "#4b5563", emoji: "🔪" },
  craft:         { bg: "#a16207", border: "#854d0e", emoji: "🏺" },
};

const DEFAULT_PIN: PinStyle = { bg: "#3b82f6", border: "#2563eb",  emoji: "📍" };
const ACC_PIN:     PinStyle = { bg: "#FFD700", border: "#B8860B", emoji: "🏠" };

function getCategoryPin(category: string | null): PinStyle {
  if (!category) return DEFAULT_PIN;
  const key = category.toLowerCase();
  for (const [k, v] of Object.entries(CATEGORY_PINS)) {
    if (key.includes(k)) return v;
  }
  return DEFAULT_PIN;
}

// ── Auto-fit bounds after first render ────────────────────────────────────────
interface LatLng { lat: number; lng: number }

function BoundsFitter({ points }: { points: LatLng[] }) {
  const map = useMap();
  const fitted = useRef(false);

  useEffect(() => {
    if (!map || points.length === 0 || fitted.current) return;
    fitted.current = true;

    if (points.length === 1) {
      map.setCenter(points[0]);
      map.setZoom(15);
      return;
    }

    // @ts-ignore — google is available once APIProvider has loaded
    const bounds = new google.maps.LatLngBounds();
    points.forEach((p) => bounds.extend(p));
    map.fitBounds(bounds, { top: 50, right: 50, bottom: 50, left: 50 });
  }, [map, points]);

  return null;
}

// ── Custom pin dot with hover tooltip ─────────────────────────────────────────
function MarkerPin({
  pin,
  hovered,
  selected,
  label,
  subtitle,
  onEnter,
  onLeave,
}: {
  pin: PinStyle;
  hovered: boolean;
  selected: boolean;
  label: string;
  subtitle?: string | null;
  onEnter: () => void;
  onLeave: () => void;
}) {
  return (
    <div
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      style={{ position: "relative", cursor: "pointer" }}
    >
      {/* Hover tooltip */}
      {hovered && !selected && (
        <div
          style={{
            position: "absolute",
            bottom: "calc(100% + 8px)",
            left: "50%",
            transform: "translateX(-50%)",
            background: "rgba(15,23,42,0.9)",
            color: "white",
            borderRadius: "7px",
            padding: "5px 9px",
            fontSize: "11px",
            whiteSpace: "nowrap",
            maxWidth: "200px",
            overflow: "hidden",
            textOverflow: "ellipsis",
            pointerEvents: "none",
            zIndex: 1000,
            boxShadow: "0 3px 10px rgba(0,0,0,0.3)",
            lineHeight: "1.4",
          }}
        >
          <div style={{ fontWeight: 700 }}>{label}</div>
          {subtitle && (
            <div style={{ color: "#94a3b8", fontSize: "10px", marginTop: "1px" }}>
              {subtitle}
            </div>
          )}
        </div>
      )}

      {/* Pin circle */}
      <div
        style={{
          width: selected ? 26 : 20,
          height: selected ? 26 : 20,
          borderRadius: "50%",
          background: pin.bg,
          border: `3px solid ${pin.border}`,
          boxShadow: selected
            ? `0 0 0 3px ${pin.bg}44, 0 4px 12px rgba(0,0,0,0.4)`
            : hovered
            ? "0 3px 10px rgba(0,0,0,0.35)"
            : "0 2px 5px rgba(0,0,0,0.25)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: selected ? "11px" : "9px",
          transform: selected ? "scale(1.15)" : hovered ? "scale(1.1)" : "scale(1)",
          transition: "transform 0.12s, box-shadow 0.12s",
        }}
      >
        {pin.emoji}
      </div>
    </div>
  );
}

// ── POI type for guaranteed coords ────────────────────────────────────────────
interface PoiWithCoords extends Poi {
  lat: number;
  lng: number;
}

interface Props {
  pois: Poi[];
  city: string;
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function PoisMapInner({ pois, city }: Props) {
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ?? "";

  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [selectedPoi, setSelectedPoi] = useState<PoiWithCoords | null>(null);
  const [selectedAcc, setSelectedAcc] = useState<string | null>(null);

  const mappablePois = pois.filter(
    (p): p is PoiWithCoords =>
      typeof p.lat === "number" && p.lat !== null &&
      typeof p.lng === "number" && p.lng !== null
  );

  const accommodation = ACCOMMODATIONS[city] ?? null;

  const allPoints: LatLng[] = [
    ...mappablePois.map((p) => ({ lat: p.lat, lng: p.lng })),
    ...(accommodation ? [{ lat: accommodation.lat, lng: accommodation.lng }] : []),
  ];

  const defaultCenter: LatLng =
    accommodation
      ? { lat: accommodation.lat, lng: accommodation.lng }
      : allPoints[0] ?? { lat: 34.6937, lng: 135.5023 };

  if (!apiKey) {
    return (
      <div style={{ width: "100%", height: "400px", borderRadius: "10px", background: "#f1f5f9", display: "flex", alignItems: "center", justifyContent: "center", color: "#9ca3af", fontSize: "0.85rem" }}>
        Google Maps API key not configured
      </div>
    );
  }

  return (
    <APIProvider apiKey={apiKey}>
      <Map
        defaultCenter={defaultCenter}
        defaultZoom={13}
        mapId="DEMO_MAP_ID"
        style={{ width: "100%", height: "400px", borderRadius: "10px" }}
        gestureHandling="greedy"
        onClick={() => { setSelectedPoi(null); setSelectedAcc(null); }}
      >
        <BoundsFitter points={allPoints} />

        {/* POI markers */}
        {mappablePois.map((poi) => {
          const pinId = `poi-${poi.id}`;
          const pin = getCategoryPin(poi.category);
          const isHov = hoveredId === pinId;
          const isSel = selectedPoi?.id === poi.id;
          return (
            <AdvancedMarker
              key={pinId}
              position={{ lat: poi.lat, lng: poi.lng }}
              onClick={() => { setSelectedPoi(poi); setSelectedAcc(null); }}
              zIndex={isSel ? 100 : 5}
            >
              <MarkerPin
                pin={pin}
                hovered={isHov}
                selected={isSel}
                label={poi.name_en}
                subtitle={poi.category ?? undefined}
                onEnter={() => setHoveredId(pinId)}
                onLeave={() => setHoveredId(null)}
              />
            </AdvancedMarker>
          );
        })}

        {/* Accommodation marker */}
        {accommodation && (
          <AdvancedMarker
            position={{ lat: accommodation.lat, lng: accommodation.lng }}
            onClick={() => { setSelectedAcc(accommodation.label); setSelectedPoi(null); }}
            zIndex={selectedAcc ? 100 : 10}
          >
            <MarkerPin
              pin={ACC_PIN}
              hovered={hoveredId === "acc"}
              selected={!!selectedAcc}
              label={accommodation.label}
              subtitle="Your accommodation"
              onEnter={() => setHoveredId("acc")}
              onLeave={() => setHoveredId(null)}
            />
          </AdvancedMarker>
        )}

        {/* InfoWindow — selected POI */}
        {selectedPoi && (
          <InfoWindow
            position={{ lat: selectedPoi.lat, lng: selectedPoi.lng }}
            onCloseClick={() => setSelectedPoi(null)}
            pixelOffset={[0, -28]}
          >
            <div style={{ maxWidth: "240px", fontFamily: "inherit" }}>
              <div style={{ fontWeight: 700, fontSize: "0.87rem", marginBottom: "2px", lineHeight: 1.3 }}>
                {selectedPoi.name_en}
              </div>
              {selectedPoi.name_ja && (
                <div style={{ fontSize: "0.75rem", color: "#6b7280", marginBottom: "4px" }}>
                  {selectedPoi.name_ja}
                </div>
              )}
              {selectedPoi.category && (
                <div style={{ fontSize: "0.72rem", display: "inline-block", padding: "1px 7px", borderRadius: "999px", background: getCategoryPin(selectedPoi.category).bg + "22", color: getCategoryPin(selectedPoi.category).border, fontWeight: 700, marginBottom: "6px" }}>
                  {selectedPoi.category}
                </div>
              )}
              {selectedPoi.description && (
                <div style={{ fontSize: "0.78rem", color: "#374151", lineHeight: 1.45, marginBottom: "4px" }}>
                  {selectedPoi.description.length > 120
                    ? selectedPoi.description.slice(0, 120) + "…"
                    : selectedPoi.description}
                </div>
              )}
              {selectedPoi.crowd_notes && (
                <div style={{ fontSize: "0.72rem", color: "#6b7280", lineHeight: 1.4, borderTop: "1px solid #f1f5f9", paddingTop: "4px" }}>
                  <strong>👥 Tips:</strong> {selectedPoi.crowd_notes.length > 100
                    ? selectedPoi.crowd_notes.slice(0, 100) + "…"
                    : selectedPoi.crowd_notes}
                </div>
              )}
              {selectedPoi.best_time && (
                <div style={{ fontSize: "0.72rem", color: "#6b7280", marginTop: "3px" }}>
                  ⏰ Best time: {selectedPoi.best_time}
                </div>
              )}
              {selectedPoi.map_url && (
                <a
                  href={selectedPoi.map_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ display: "inline-block", marginTop: "6px", fontSize: "0.75rem", color: "#2563eb", fontWeight: 600 }}
                >
                  🗺️ Open in Maps
                </a>
              )}
            </div>
          </InfoWindow>
        )}

        {/* InfoWindow — accommodation */}
        {selectedAcc && accommodation && (
          <InfoWindow
            position={{ lat: accommodation.lat, lng: accommodation.lng }}
            onCloseClick={() => setSelectedAcc(null)}
            pixelOffset={[0, -28]}
          >
            <div style={{ fontFamily: "inherit" }}>
              <div style={{ fontWeight: 700, fontSize: "0.87rem", marginBottom: "2px" }}>
                🏠 {accommodation.label}
              </div>
              <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>
                Your accommodation in {city.charAt(0).toUpperCase() + city.slice(1)}
              </div>
            </div>
          </InfoWindow>
        )}
      </Map>
    </APIProvider>
  );
}
