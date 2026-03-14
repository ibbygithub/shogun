"use client";

import { useState } from "react";
import type { Poi } from "@/lib/types";
import ChatPanel from "@/components/chat/ChatPanel";

interface KnowledgeData {
  poi: Poi;
  summary: string | null;
  youtube_query: string;
  suggested_searches: string[];
  booking_url: string | null;
}

interface Props {
  data: KnowledgeData;
}

export default function KnowledgeDeepDive({ data }: Props) {
  const [showChat, setShowChat] = useState(false);
  const { poi } = data;

  return (
    <div style={{ maxWidth: "720px", margin: "0 auto", padding: "1.5rem" }}>
      {/* Header */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 900 }}>{poi.name_en}</h1>
        {poi.name_ja && <div style={{ fontSize: "1rem", color: "#6b7280", marginTop: "0.25rem" }}>{poi.name_ja}</div>}
        <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem", flexWrap: "wrap" }}>
          {poi.tags?.map((tag) => (
            <span key={tag} style={{ background: "#eff6ff", color: "#1d4ed8", fontSize: "0.75rem", padding: "2px 8px", borderRadius: "4px" }}>
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* Summary */}
      {data.summary && (
        <div style={{ background: "white", borderRadius: "10px", padding: "1rem", marginBottom: "1rem", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
          <p style={{ lineHeight: 1.6, color: "#374151" }}>{data.summary}</p>
        </div>
      )}

      {/* Practical info */}
      <div style={{ background: "white", borderRadius: "10px", padding: "1rem", marginBottom: "1rem", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
        <h3 style={{ fontWeight: 700, marginBottom: "0.5rem" }}>Practical Info</h3>
        {poi.best_time && <div style={{ fontSize: "0.875rem", marginBottom: "0.25rem" }}>⏰ <strong>Best time:</strong> {poi.best_time}</div>}
        {poi.crowd_notes && <div style={{ fontSize: "0.875rem", marginBottom: "0.25rem" }}>👥 <strong>Crowds:</strong> {poi.crowd_notes}</div>}
        {data.booking_url && (
          <a href={data.booking_url} target="_blank" rel="noopener noreferrer"
            style={{ display: "inline-block", marginTop: "0.5rem", color: "var(--city-accent)", fontSize: "0.875rem", fontWeight: 600 }}>
            View on map →
          </a>
        )}
      </div>

      {/* Learn more */}
      <div style={{ background: "white", borderRadius: "10px", padding: "1rem", marginBottom: "1rem", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
        <h3 style={{ fontWeight: 700, marginBottom: "0.75rem" }}>Learn More</h3>
        <a
          href={`https://www.youtube.com/results?search_query=${encodeURIComponent(data.youtube_query)}`}
          target="_blank" rel="noopener noreferrer"
          style={{
            display: "inline-flex", alignItems: "center", gap: "0.5rem",
            background: "#ff0000", color: "white", padding: "0.5rem 1rem",
            borderRadius: "8px", fontWeight: 600, fontSize: "0.85rem", textDecoration: "none",
            marginBottom: "0.75rem",
          }}
        >
          ▶ Watch on YouTube
        </a>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.375rem" }}>
          {data.suggested_searches.map((q, i) => (
            <a key={i}
              href={`https://www.google.com/search?q=${encodeURIComponent(q)}`}
              target="_blank" rel="noopener noreferrer"
              style={{ fontSize: "0.85rem", color: "#1d4ed8" }}
            >
              🔍 {q}
            </a>
          ))}
        </div>
      </div>

      {/* Ask Shogun */}
      <div style={{ background: "white", borderRadius: "10px", overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
        <button
          onClick={() => setShowChat(!showChat)}
          style={{
            width: "100%", padding: "0.875rem 1rem",
            background: "none", border: "none", cursor: "pointer",
            display: "flex", justifyContent: "space-between", alignItems: "center",
            fontWeight: 700, fontSize: "0.95rem",
          }}
        >
          <span>💬 Ask Shogun about {poi.name_en}</span>
          <span>{showChat ? "▲" : "▼"}</span>
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
