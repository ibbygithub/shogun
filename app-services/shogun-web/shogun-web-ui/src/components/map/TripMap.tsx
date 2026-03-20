"use client";

import dynamic from "next/dynamic";

// Dynamic import — @vis.gl/react-google-maps references browser globals (window, document).
// ssr: false prevents server-side rendering errors.
const TripMapInner = dynamic(() => import("./TripMapInner"), {
  ssr: false,
  loading: () => (
    <div
      style={{
        width: "100%",
        height: "600px",
        background: "#f1f5f9",
        borderRadius: "12px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "#9ca3af",
        fontSize: "0.9rem",
      }}
    >
      Loading map…
    </div>
  ),
});

interface TripMapProps {
  height?: string;
}

export default function TripMap({ height }: TripMapProps) {
  return <TripMapInner height={height} />;
}
