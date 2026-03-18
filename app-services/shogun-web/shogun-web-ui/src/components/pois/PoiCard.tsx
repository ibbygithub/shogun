"use client";

import { useState } from "react";
import Link from "next/link";
import type { Poi } from "@/lib/types";
import { api } from "@/lib/api";

interface Props {
  poi: Poi;
}

// City pastel tile backgrounds
const CITY_BG: Record<string, string> = {
  osaka:     "#FFF0E6",
  nara:      "#E8F5E9",
  kanazawa:  "#FFF8E1",
  tokyo:     "#EEF2FF",
  kyoto:     "#FCE4EC",
};

// Category badge color mappings { bg, text }
function getCategoryBadge(category: string | null): { bg: string; text: string; label: string } | null {
  if (!category) return null;
  const c = category.toLowerCase();
  if (c.includes("temple") || c.includes("shrine")) {
    return { bg: "#FEE2E2", text: "#991B1B", label: category };
  }
  if (c.includes("food") || c.includes("restaurant") || c.includes("ramen") || c.includes("eat")) {
    return { bg: "#FED7AA", text: "#9A3412", label: category };
  }
  if (c.includes("shop")) {
    return { bg: "#EDE9FE", text: "#5B21B6", label: category };
  }
  if (c.includes("nature") || c.includes("park") || c.includes("garden")) {
    return { bg: "#D1FAE5", text: "#065F46", label: category };
  }
  if (c.includes("museum") || c.includes("culture") || c.includes("art") || c.includes("history")) {
    return { bg: "#DBEAFE", text: "#1E40AF", label: category };
  }
  if (c.includes("entertainment") || c.includes("theatre") || c.includes("theater") || c.includes("show")) {
    return { bg: "#FCE7F3", text: "#9D174D", label: category };
  }
  if (c.includes("transit") || c.includes("station") || c.includes("transport")) {
    return { bg: "#E5E7EB", text: "#374151", label: category };
  }
  if (c.includes("electronics") || c.includes("tech") || c.includes("akihabara")) {
    return { bg: "#CFFAFE", text: "#0E7490", label: category };
  }
  return { bg: "#F3F4F6", text: "#4B5563", label: category };
}

type SaveState = "idle" | "saving" | "saved" | "error";

export default function PoiCard({ poi }: Props) {
  const cityBg = (poi.city && CITY_BG[poi.city]) ? CITY_BG[poi.city] : "#F5F5F5";
  const badge = getCategoryBadge(poi.category);
  const [saveState, setSaveState] = useState<SaveState>("idle");

  async function handleSave(e: React.MouseEvent) {
    // Don't trigger the card's Link navigation
    e.preventDefault();
    e.stopPropagation();
    if (saveState !== "idle") return;
    setSaveState("saving");
    try {
      await api.wishlist.create({ city: poi.city || undefined, description: poi.name_en });
      setSaveState("saved");
      setTimeout(() => setSaveState("idle"), 2000);
    } catch {
      setSaveState("error");
      setTimeout(() => setSaveState("idle"), 3000);
    }
  }

  const saveLabel =
    saveState === "saving" ? "…" :
    saveState === "saved"  ? "✓ Saved" :
    saveState === "error"  ? "⚠ Failed" :
    "⭐ Save";

  const saveBg =
    saveState === "saved"  ? "#d1fae5" :
    saveState === "error"  ? "#fee2e2" :
    "rgba(255,255,255,0.75)";

  const saveColor =
    saveState === "saved"  ? "#065f46" :
    saveState === "error"  ? "#991b1b" :
    "#374151";

  return (
    <Link href={`/pois/${poi.id}`} style={{ textDecoration: "none" }}>
      <div style={{
        background: cityBg,
        borderRadius: "10px",
        padding: "0.875rem",
        boxShadow: "0 1px 3px rgba(0,0,0,0.07)",
        cursor: "pointer",
        transition: "transform 0.15s, box-shadow 0.15s",
        position: "relative",
      }}>
        {/* Category badge */}
        {badge && (
          <div style={{ marginBottom: "0.4rem" }}>
            <span style={{
              display: "inline-block",
              fontSize: "0.7rem",
              fontWeight: 700,
              background: badge.bg,
              color: badge.text,
              padding: "3px 10px",
              borderRadius: "9999px",
              letterSpacing: "0.02em",
              textTransform: "capitalize",
            }}>
              {badge.label}
            </span>
          </div>
        )}

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "0.5rem" }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "#111827" }}>
              {poi.name_en}
            </div>
            {poi.name_ja && (
              <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>{poi.name_ja}</div>
            )}
          </div>
          {poi.city && (
            <span style={{
              fontSize: "0.7rem",
              background: "rgba(255,255,255,0.7)",
              color: "#475569",
              padding: "2px 8px",
              borderRadius: "9999px",
              whiteSpace: "nowrap",
            }}>
              {poi.city}
            </span>
          )}
        </div>

        {poi.description && (
          <p style={{ marginTop: "0.4rem", fontSize: "0.8rem", color: "#4b5563", lineHeight: 1.4,
            display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden",
          }}>
            {poi.description}
          </p>
        )}

        <div style={{ marginTop: "0.5rem", display: "flex", gap: "0.375rem", flexWrap: "wrap" }}>
          {poi.tags?.slice(0, 4).map((tag) => (
            <span key={tag} style={{
              fontSize: "0.7rem",
              background: "rgba(255,255,255,0.65)",
              color: "#1d4ed8",
              padding: "2px 6px",
              borderRadius: "4px",
            }}>
              {tag}
            </span>
          ))}
        </div>

        {poi.best_time && (
          <div style={{ marginTop: "0.375rem", fontSize: "0.75rem", color: "#6b7280" }}>
            ⏰ {poi.best_time}
          </div>
        )}

        {/* Save to collection button */}
        <div style={{ marginTop: "0.625rem", display: "flex", justifyContent: "flex-end" }}>
          <button
            onClick={handleSave}
            disabled={saveState === "saving"}
            style={{
              fontSize: "0.72rem",
              fontWeight: 600,
              background: saveBg,
              color: saveColor,
              border: "1px solid rgba(0,0,0,0.1)",
              borderRadius: "6px",
              padding: "3px 10px",
              cursor: saveState === "saving" ? "default" : "pointer",
              transition: "background 0.2s, color 0.2s",
            }}
          >
            {saveLabel}
          </button>
        </div>
      </div>
    </Link>
  );
}
