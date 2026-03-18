"use client";

import { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { Poi } from "@/lib/types";

// Fix default marker icons in Next.js — Leaflet's default icon URLs break in bundled builds
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

// Custom icon for accommodation (red)
const accommodationIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
  iconRetinaUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

// Custom icon for POIs (blue — default)
const poiIcon = new L.Icon({
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const ACCOMMODATION: Record<string, { lat: number; lng: number; label: string }> = {
  osaka:    { lat: 34.7255, lng: 135.5185, label: "Tenjinbashi Queen Airbnb" },
  kanazawa: { lat: 36.5613, lng: 136.6562, label: "Hotel Sanraku Kanazawa" },
  tokyo:    { lat: 35.7358, lng: 139.7283, label: "Sugamo Airbnb" },
  nara:     { lat: 34.6851, lng: 135.8048, label: "Nara Park (day trip)" },
};

interface PoiWithCoords extends Poi {
  lat: number;  // required — guaranteed non-null after filter
  lng: number;
}

interface Props {
  pois: Poi[];
  city: string;
}

// Component that auto-fits bounds after render
function BoundsFitter({ points }: { points: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (points.length === 0) return;
    if (points.length === 1) {
      map.setView(points[0], 14);
      return;
    }
    const bounds = L.latLngBounds(points.map((p) => L.latLng(p[0], p[1])));
    map.fitBounds(bounds, { padding: [40, 40] });
  }, [map, points]);
  return null;
}

export default function PoisMapInner({ pois, city }: Props) {
  // Filter to POIs that have lat/lng (Agent A adds these; guard against null/undefined)
  const mappablePois = pois.filter(
    (p): p is PoiWithCoords =>
      typeof p.lat === "number" && p.lat !== null &&
      typeof p.lng === "number" && p.lng !== null
  );

  const accommodation = ACCOMMODATION[city] ?? null;

  // Build all coordinate points for bounds fitting
  const allPoints: [number, number][] = [
    ...mappablePois.map((p) => [p.lat, p.lng] as [number, number]),
    ...(accommodation ? [[accommodation.lat, accommodation.lng] as [number, number]] : []),
  ];

  // Default center: use accommodation if available, else first POI, else Osaka
  const defaultCenter: [number, number] =
    allPoints.length > 0
      ? allPoints[0]
      : [34.6937, 135.5023];

  return (
    <MapContainer
      center={defaultCenter}
      zoom={13}
      style={{ width: "100%", height: "400px", borderRadius: "10px" }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <BoundsFitter points={allPoints} />

      {/* POI markers */}
      {mappablePois.map((poi) => (
        <Marker key={poi.id} position={[poi.lat, poi.lng]} icon={poiIcon}>
          <Popup>
            <div style={{ minWidth: "160px" }}>
              <strong style={{ fontSize: "0.85rem" }}>{poi.name_en}</strong>
              {poi.name_ja && (
                <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>{poi.name_ja}</div>
              )}
              {poi.category && (
                <div style={{ fontSize: "0.75rem", marginTop: "0.2rem", color: "#374151" }}>
                  {poi.category}
                </div>
              )}
              {poi.crowd_notes && (
                <div style={{ fontSize: "0.72rem", color: "#6b7280", marginTop: "0.25rem", lineHeight: 1.3 }}>
                  {poi.crowd_notes.substring(0, 100)}{poi.crowd_notes.length > 100 ? "…" : ""}
                </div>
              )}
            </div>
          </Popup>
        </Marker>
      ))}

      {/* Accommodation marker */}
      {accommodation && (
        <Marker position={[accommodation.lat, accommodation.lng]} icon={accommodationIcon}>
          <Popup>
            <div>
              <strong style={{ fontSize: "0.85rem" }}>🏠 Your accommodation</strong>
              <div style={{ fontSize: "0.78rem", color: "#374151", marginTop: "0.2rem" }}>
                {accommodation.label}
              </div>
            </div>
          </Popup>
        </Marker>
      )}
    </MapContainer>
  );
}
