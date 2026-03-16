"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import SakuraStatus from "@/components/ambient/SakuraStatus";

interface SakuraResult {
  title: string;
  url: string;
  summary: string;
  score: number;
}

interface SakuraData {
  city: string;
  results: SakuraResult[];
  query_time: string;
  error?: string;
}

export default function BlossomWidget() {
  const [osakaData, setOsakaData] = useState<SakuraData | null>(null);
  const [tokyoData, setTokyoData] = useState<SakuraData | null>(null);
  const [loadingOsaka, setLoadingOsaka] = useState(true);
  const [loadingTokyo, setLoadingTokyo] = useState(true);

  useEffect(() => {
    api.ambient.sakura("osaka")
      .then((d) => setOsakaData(d as SakuraData))
      .catch(() => setOsakaData(null))
      .finally(() => setLoadingOsaka(false));

    api.ambient.sakura("tokyo")
      .then((d) => setTokyoData(d as SakuraData))
      .catch(() => setTokyoData(null))
      .finally(() => setLoadingTokyo(false));
  }, []);

  return (
    <div style={{ background: "white", borderRadius: "12px", padding: "1rem", boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
      <div style={{ fontWeight: 700, marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
        🌸 Cherry Blossom Forecast 2026
      </div>
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: "0.75rem",
      }}
        className="blossom-widget-grid"
      >
        <SakuraStatus data={osakaData} loading={loadingOsaka} />
        <SakuraStatus data={tokyoData} loading={loadingTokyo} />
      </div>
      <style>{`
        @media (max-width: 600px) {
          .blossom-widget-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
}
