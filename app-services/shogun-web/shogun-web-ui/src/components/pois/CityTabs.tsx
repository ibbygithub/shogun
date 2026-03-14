"use client";

import { CITIES } from "@/lib/cities";

const ALL_CITIES = ["all", ...Object.keys(CITIES)];

interface Props {
  active: string;
  onChange: (city: string) => void;
}

export default function CityTabs({ active, onChange }: Props) {
  return (
    <div style={{ display: "flex", gap: "0", borderBottom: "2px solid #e5e7eb", padding: "0 1rem" }}>
      {ALL_CITIES.map((c) => {
        const label = c === "all" ? "All" : CITIES[c as keyof typeof CITIES]?.name ?? c;
        const isActive = active === c;
        return (
          <button key={c} onClick={() => onChange(c)}
            style={{
              padding: "0.625rem 1rem",
              fontWeight: isActive ? 700 : 400,
              color: isActive ? "var(--city-accent)" : "#6b7280",
              borderBottom: isActive ? "2px solid var(--city-accent)" : "2px solid transparent",
              marginBottom: "-2px",
              background: "none",
              border: "none",
              borderBottomStyle: "solid",
              cursor: "pointer",
              fontSize: "0.875rem",
              transition: "color 0.15s",
            }}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}
