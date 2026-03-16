"use client";

interface Props {
  lat: number;
  lon: number;
  city: string;
}

export default function WindyRadar({ lat, lon, city }: Props) {
  const windyUrl =
    `https://embed.windy.com/embed2.html` +
    `?lat=${lat}&lon=${lon}&zoom=8&level=surface&overlay=rain` +
    `&menu=&message=&marker=&calendar=&pressure=&type=map` +
    `&location=coordinates&detail=&detailLat=${lat}&detailLon=${lon}` +
    `&width=650&height=450&metricWind=default&metricTemp=%C2%B0C&radarRange=-1`;

  return (
    <div style={{
      background: "white",
      borderRadius: "12px",
      overflow: "hidden",
      boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
    }}>
      <div style={{
        padding: "0.625rem 1rem",
        fontWeight: 700,
        fontSize: "0.85rem",
        borderBottom: "1px solid #f3f4f6",
        display: "flex",
        alignItems: "center",
        gap: "0.4rem",
      }}>
        🌧️ Rain Radar · {city.charAt(0).toUpperCase() + city.slice(1)}
      </div>
      <iframe
        src={windyUrl}
        width="100%"
        height="300"
        frameBorder="0"
        title={`Weather radar - ${city}`}
        style={{ display: "block" }}
      />
    </div>
  );
}
