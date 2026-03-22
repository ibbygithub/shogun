"use client";

import { useState } from "react";
import type { Poi, PoiGuide } from "@/lib/types";
import ChatPanel from "@/components/chat/ChatPanel";

interface Props {
  poi: Poi;
  guide: PoiGuide;
}

const TYPE_LABELS: Record<string, string> = {
  museum: "Museum",
  shrine: "Shrine",
  temple: "Temple",
  shopping_district: "Shopping",
  park: "Park / Garden",
  landmark: "Landmark",
  neighborhood: "Neighborhood",
  restaurant: "Food & Drink",
  event: "Experience",
};

const TIME_LABELS: Record<string, string> = {
  quick_stop: "Under 30 min",
  standard_visit: "1-2 hours",
  deep_visit: "2-4 hours",
};

const cardStyle: React.CSSProperties = {
  background: "white",
  borderRadius: "10px",
  padding: "1rem",
  marginBottom: "1rem",
  boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
};

const headingStyle: React.CSSProperties = {
  fontWeight: 700,
  marginBottom: "0.5rem",
  fontSize: "0.95rem",
};

const bodyStyle: React.CSSProperties = {
  color: "#374151",
  lineHeight: 1.6,
  fontSize: "0.9rem",
  whiteSpace: "pre-line",
};

export default function PoiGuideView({ poi, guide }: Props) {
  const [showChat, setShowChat] = useState(false);
  const [showSources, setShowSources] = useState(false);

  return (
    <div style={{ maxWidth: "720px", margin: "0 auto", padding: "1.5rem" }}>
      {/* Header */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 900, marginBottom: "0.25rem" }}>
          {poi.name_en}
        </h1>
        {poi.name_ja && (
          <div style={{ fontSize: "1rem", color: "#6b7280", marginTop: "0.25rem" }}>
            {poi.name_ja}
          </div>
        )}
        <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
          <span
            style={{
              background: "#dbeafe",
              color: "#1e40af",
              fontSize: "0.75rem",
              padding: "2px 10px",
              borderRadius: "9999px",
              fontWeight: 600,
            }}
          >
            {TYPE_LABELS[guide.poi_type] || guide.poi_type}
          </span>
          {poi.category && (
            <span
              style={{
                background: "#f3f4f6",
                color: "#374151",
                fontSize: "0.75rem",
                padding: "2px 8px",
                borderRadius: "4px",
              }}
            >
              {poi.category}
            </span>
          )}
          {poi.tags?.map((tag) => (
            <span
              key={tag}
              style={{
                background: "#eff6ff",
                color: "#1d4ed8",
                fontSize: "0.75rem",
                padding: "2px 8px",
                borderRadius: "4px",
              }}
            >
              {tag}
            </span>
          ))}
          {guide.completeness && (
            <span
              style={{
                fontSize: "0.7rem",
                color: guide.completeness === "full" ? "#059669" : "#d97706",
                marginLeft: "auto",
              }}
            >
              {guide.completeness === "full" ? "Full guide" : "Partial guide"}
            </span>
          )}
        </div>
      </div>

      {/* Photo gallery — horizontal scroll */}
      {guide.photos && guide.photos.length > 0 && (
        <div
          style={{
            display: "flex",
            gap: "0.5rem",
            overflowX: "auto",
            marginBottom: "1rem",
            paddingBottom: "0.5rem",
          }}
        >
          {guide.photos.map((photo, i) => {
            const src = photo.url || "";
            if (!src) return null;
            return (
              <img
                key={i}
                src={src}
                alt={`${poi.name_en} photo ${i + 1}`}
                style={{
                  height: "160px",
                  borderRadius: "8px",
                  objectFit: "cover",
                  flexShrink: 0,
                }}
              />
            );
          })}
        </div>
      )}

      {/* Overview */}
      {guide.overview && (
        <div style={cardStyle}>
          <h3 style={headingStyle}>Overview</h3>
          <p style={bodyStyle}>{guide.overview}</p>
        </div>
      )}

      {/* Why Go */}
      {guide.why_go && (
        <div style={cardStyle}>
          <h3 style={headingStyle}>Why Go</h3>
          <p style={bodyStyle}>{guide.why_go}</p>
        </div>
      )}

      {/* What's There */}
      {guide.whats_there && (
        <div style={cardStyle}>
          <h3 style={headingStyle}>What&apos;s There</h3>
          <p style={bodyStyle}>{guide.whats_there}</p>
        </div>
      )}

      {/* Practical Info */}
      {(guide.hours_info || guide.admission_info || guide.time_estimate) && (
        <div style={cardStyle}>
          <h3 style={headingStyle}>Practical Info</h3>
          {guide.hours_info && (
            <div style={{ fontSize: "0.875rem", marginBottom: "0.5rem", color: "#374151" }}>
              <strong>Hours:</strong> {guide.hours_info}
              {guide.hours_verified && (
                <span style={{ color: "#059669", marginLeft: "0.5rem", fontSize: "0.75rem" }}>
                  Verified
                </span>
              )}
            </div>
          )}
          {guide.admission_info && (
            <div style={{ fontSize: "0.875rem", marginBottom: "0.5rem", color: "#374151" }}>
              <strong>Admission:</strong> {guide.admission_info}
            </div>
          )}
          {guide.time_estimate && (
            <div style={{ fontSize: "0.875rem", color: "#374151" }}>
              <strong>Time needed:</strong>{" "}
              {TIME_LABELS[guide.time_estimate] || guide.time_estimate}
            </div>
          )}
          {guide.official_url && (
            <a
              href={guide.official_url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: "inline-block",
                marginTop: "0.5rem",
                color: "var(--city-accent, #1d4ed8)",
                fontSize: "0.85rem",
                fontWeight: 600,
                textDecoration: "none",
              }}
            >
              Official website &rarr;
            </a>
          )}
        </div>
      )}

      {/* Getting There */}
      {guide.transit_info && (
        <div style={cardStyle}>
          <h3 style={headingStyle}>Getting There</h3>
          <p style={bodyStyle}>{guide.transit_info}</p>
          {poi.lat && poi.lng && (
            <a
              href={`https://maps.google.com/?q=${poi.lat},${poi.lng}`}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: "inline-block",
                marginTop: "0.5rem",
                color: "var(--city-accent, #1d4ed8)",
                fontSize: "0.85rem",
                fontWeight: 600,
                textDecoration: "none",
              }}
            >
              View on Google Maps &rarr;
            </a>
          )}
        </div>
      )}

      {/* Tips */}
      {guide.tips && (
        <div style={cardStyle}>
          <h3 style={headingStyle}>Tips</h3>
          <p style={bodyStyle}>{guide.tips}</p>
        </div>
      )}

      {/* Your Trip — highlighted card */}
      {guide.trip_context && (
        <div
          style={{
            ...cardStyle,
            background: "#fffbeb",
            border: "1px solid #fde68a",
          }}
        >
          <h3 style={{ ...headingStyle, color: "#92400e" }}>For Your Trip</h3>
          <p style={{ ...bodyStyle, color: "#78350f" }}>{guide.trip_context}</p>
        </div>
      )}

      {/* Sources accordion */}
      {guide.sources && guide.sources.length > 0 && (
        <div style={cardStyle}>
          <button
            onClick={() => setShowSources(!showSources)}
            style={{
              width: "100%",
              background: "none",
              border: "none",
              cursor: "pointer",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: 0,
              fontWeight: 700,
              fontSize: "0.95rem",
            }}
          >
            <span>Sources ({guide.sources.length})</span>
            <span>{showSources ? "\u25B2" : "\u25BC"}</span>
          </button>
          {showSources && (
            <div style={{ marginTop: "0.5rem" }}>
              {guide.sources.map((src, i) => (
                <a
                  key={i}
                  href={src.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: "block",
                    fontSize: "0.8rem",
                    color: "#1d4ed8",
                    marginBottom: "0.25rem",
                    textDecoration: "none",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {src.title || src.url}
                </a>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Ask Shogun */}
      <div
        style={{
          background: "white",
          borderRadius: "10px",
          overflow: "hidden",
          boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
        }}
      >
        <button
          onClick={() => setShowChat(!showChat)}
          style={{
            width: "100%",
            padding: "0.875rem 1rem",
            background: "none",
            border: "none",
            cursor: "pointer",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            fontWeight: 700,
            fontSize: "0.95rem",
          }}
        >
          <span>Ask Shogun about {poi.name_en}</span>
          <span>{showChat ? "\u25B2" : "\u25BC"}</span>
        </button>
        {showChat && (
          <div style={{ height: "400px", borderTop: "1px solid #e5e7eb" }}>
            <ChatPanel />
          </div>
        )}
      </div>
    </div>
  );
}
