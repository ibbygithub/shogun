import Link from "next/link";
import type { Poi } from "@/lib/types";

interface Props {
  poi: Poi;
}

export default function PoiCard({ poi }: Props) {
  return (
    <Link href={`/pois/${poi.id}`} style={{ textDecoration: "none" }}>
      <div style={{
        background: "white",
        borderRadius: "10px",
        padding: "0.875rem",
        boxShadow: "0 1px 3px rgba(0,0,0,0.07)",
        cursor: "pointer",
        transition: "transform 0.15s, box-shadow 0.15s",
      }}>
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
              background: "#f1f5f9",
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
              background: "#eff6ff",
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
      </div>
    </Link>
  );
}
