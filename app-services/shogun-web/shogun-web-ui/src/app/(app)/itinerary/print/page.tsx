"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ItineraryLeg } from "@/lib/types";

export const dynamic = "force-dynamic";

/* ── City color mapping ── */
const CITY_COLORS: Record<string, { bg: string; text: string; border: string; print: string }> = {
  osaka:    { bg: "bg-red-100",    text: "text-red-800",    border: "border-red-300",    print: "Osaka" },
  kanazawa: { bg: "bg-yellow-100", text: "text-yellow-800", border: "border-yellow-300", print: "Kanazawa" },
  tokyo:    { bg: "bg-blue-100",   text: "text-blue-800",   border: "border-blue-300",   print: "Tokyo" },
  nara:     { bg: "bg-green-100",  text: "text-green-800",  border: "border-green-300",  print: "Nara" },
};

function cityStyle(city: string | null) {
  const key = (city || "").toLowerCase();
  return CITY_COLORS[key] || { bg: "bg-gray-100", text: "text-gray-700", border: "border-gray-300", print: city || "—" };
}

/* ── Format helpers ── */
function fmtDate(iso: string): string {
  const d = new Date(iso + "T12:00:00");
  return d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
}

function groupByDate(legs: ItineraryLeg[]): Map<string, ItineraryLeg[]> {
  const map = new Map<string, ItineraryLeg[]>();
  for (const leg of legs) {
    const key = leg.date_start || "no-date";
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(leg);
  }
  return map;
}

/* ── Accommodations data ── */
const ACCOMMODATIONS = [
  { dates: "Mar 24 – 29", name: "Tenjinbashi Queen Airbnb", area: "Kita-ku, Osaka", ja: "大阪市北区浪花町10-12" },
  { dates: "Mar 30 – 31", name: "Hotel Sanraku", area: "Owaricho, Kanazawa", ja: "石川県金沢市尾張町1-1-1" },
  { dates: "Apr 1 – 8",   name: "Sugamo Airbnb", area: "Toshima-ku, Tokyo", ja: "東京都豊島区巣鴨4-37-6" },
];

/* ── Main component ── */
export default function PrintItineraryPage() {
  const [legs, setLegs] = useState<ItineraryLeg[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.itinerary
      .list()
      .then((d) => setLegs(d as ItineraryLeg[]))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const grouped = groupByDate(legs);

  /* Track city changes for page-break hints */
  let lastCity: string | null = null;

  return (
    <>
      {/* Print-specific styles */}
      <style>{`
        @media print {
          /* Hide app shell chrome */
          .app-shell > aside,
          .app-shell > nav,
          .mobile-tab-bar,
          [data-print-hide] {
            display: none !important;
          }
          .main-content {
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            max-width: 100% !important;
          }
          .app-shell {
            display: block !important;
          }
          /* Clean print styling */
          body {
            font-size: 11pt;
            color: #000 !important;
            background: #fff !important;
          }
          .print-page {
            padding: 0 !important;
          }
          .print-city-break {
            page-break-before: always;
          }
          .print-no-break {
            page-break-inside: avoid;
          }
          /* Remove colored backgrounds in print — use borders instead */
          .city-badge-print {
            background: #fff !important;
            border: 1.5pt solid #000 !important;
            color: #000 !important;
          }
        }
      `}</style>

      <div className="print-page max-w-3xl mx-auto px-4 py-6 sm:px-6">
        {/* Header + Print button */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-black tracking-tight">
              Shogun Trip Itinerary
              <span className="ml-2 text-base font-normal text-gray-500">旅程表</span>
            </h1>
            <p className="text-sm text-gray-500 mt-1">Mar 23 – Apr 9, 2026</p>
          </div>
          <button
            data-print-hide
            onClick={() => window.print()}
            className="px-4 py-2 bg-gray-900 text-white text-sm font-semibold rounded-lg hover:bg-gray-700 transition-colors print:hidden"
          >
            Print
          </button>
        </div>

        {/* ── Emergency Info Block ── */}
        <div className="print-no-break border border-red-300 rounded-lg p-4 mb-6 bg-red-50">
          <h2 className="text-sm font-bold uppercase tracking-wide text-red-800 mb-2">
            Emergency Information / 緊急連絡先
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            <div>
              <p className="font-semibold">Japan Emergency</p>
              <p>Police 警察: <span className="font-mono font-bold">110</span></p>
              <p>Fire / Ambulance 消防・救急: <span className="font-mono font-bold">119</span></p>
            </div>
            <div>
              <p className="font-semibold">US Embassy Tokyo</p>
              <p>アメリカ大使館</p>
              <p className="font-mono font-bold">03-3224-5000</p>
            </div>
          </div>
        </div>

        {/* ── Accommodations Block ── */}
        <div className="print-no-break border border-gray-200 rounded-lg p-4 mb-6 bg-gray-50">
          <h2 className="text-sm font-bold uppercase tracking-wide text-gray-700 mb-3">
            Accommodations / 宿泊先
          </h2>
          <div className="space-y-3">
            {ACCOMMODATIONS.map((a) => (
              <div key={a.dates} className="text-sm">
                <p className="font-semibold">{a.dates}: {a.name}</p>
                <p className="text-gray-600">{a.area}</p>
                <p className="text-gray-800" lang="ja">{a.ja}</p>
              </div>
            ))}
          </div>
        </div>

        {/* ── Loading / Error states ── */}
        {loading && (
          <div className="text-gray-500 py-8 text-center">Loading itinerary…</div>
        )}
        {error && (
          <div className="text-red-600 py-4 text-center text-sm">Failed to load: {error}</div>
        )}
        {!loading && !error && legs.length === 0 && (
          <div className="text-gray-400 py-8 text-center">No itinerary items found.</div>
        )}

        {/* ── Itinerary legs grouped by date ── */}
        {Array.from(grouped.entries()).map(([dateKey, datelegs]) => {
          const currentCity = datelegs[0]?.city?.toLowerCase() || null;
          const cityChanged = lastCity !== null && currentCity !== lastCity;
          lastCity = currentCity;

          return (
            <div
              key={dateKey}
              className={cityChanged ? "print-city-break" : ""}
            >
              {/* Date header */}
              <div className="flex items-center gap-2 mt-6 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                  {dateKey !== "no-date" ? fmtDate(dateKey) : "Unscheduled"}
                </span>
                <div className="flex-1 border-b border-gray-200" />
              </div>

              {/* Legs for this date */}
              <div className="space-y-3">
                {datelegs.map((leg) => {
                  const cs = cityStyle(leg.city);
                  return (
                    <div
                      key={leg.id}
                      className={`print-no-break border rounded-lg p-3 ${cs.border} bg-white`}
                    >
                      {/* Title row with city badge */}
                      <div className="flex items-start gap-2">
                        {leg.city && (
                          <span
                            className={`city-badge-print inline-block text-xs font-bold px-2 py-0.5 rounded ${cs.bg} ${cs.text}`}
                          >
                            {leg.city.charAt(0).toUpperCase() + leg.city.slice(1)}
                          </span>
                        )}
                        <span className="font-semibold text-sm leading-snug">{leg.title}</span>
                      </div>

                      {/* Description */}
                      {leg.description && (
                        <p className="text-sm text-gray-600 mt-1">{leg.description}</p>
                      )}

                      {/* Addresses — bilingual */}
                      {(leg.address_en || leg.address_ja) && (
                        <div className="mt-2 text-xs text-gray-600 space-y-0.5">
                          {leg.address_en && <p>{leg.address_en}</p>}
                          {leg.address_ja && <p lang="ja">{leg.address_ja}</p>}
                        </div>
                      )}

                      {/* Confirmation number */}
                      {leg.confirmation_number && (
                        <p className="mt-2 text-xs">
                          <span className="text-gray-500">Confirmation 予約番号: </span>
                          <span className="font-mono font-bold">{leg.confirmation_number}</span>
                        </p>
                      )}

                      {/* Notes */}
                      {leg.notes && (
                        <p className="mt-1 text-xs text-gray-500 italic">{leg.notes}</p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}

        {/* Footer */}
        <div className="mt-10 pt-4 border-t border-gray-200 text-center text-xs text-gray-400">
          Generated by Shogun / 将軍 — AI Travel Concierge
        </div>
      </div>
    </>
  );
}
