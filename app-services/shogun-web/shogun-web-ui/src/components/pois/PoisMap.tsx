"use client";

import dynamic from "next/dynamic";
import type { Poi } from "@/lib/types";

// Leaflet requires window — must be loaded client-side only
const PoisMapInner = dynamic(() => import("./PoisMapInner"), {
  ssr: false,
  loading: () => (
    <div style={{
      width: "100%",
      height: "400px",
      borderRadius: "10px",
      background: "#f1f5f9",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: "#94a3b8",
      fontSize: "0.85rem",
    }}>
      Loading map…
    </div>
  ),
});

interface Props {
  pois: Poi[];
  city: string;
}

export default function PoisMap({ pois, city }: Props) {
  return <PoisMapInner pois={pois} city={city} />;
}
