"use client";

import { useState, useEffect } from "react";

interface ChecklistItem {
  text: string;
}

interface ChecklistCategory {
  id: string;
  label: string;
  items: ChecklistItem[];
}

const CATEGORIES: ChecklistCategory[] = [
  {
    id: "documents",
    label: "Documents",
    items: [
      { text: "Passport (valid >6 months)" },
      { text: "Travel insurance documents" },
      { text: "Hotel & Airbnb confirmation printouts" },
      { text: "Ghibli Museum timed-entry tickets" },
      { text: "Japan emergency contact list" },
    ],
  },
  {
    id: "money",
    label: "Money & Cards",
    items: [
      { text: "Credit card (notify bank of Japan travel)" },
      { text: "Backup card" },
      { text: "¥50,000+ yen cash (many places cash-only)" },
      { text: "IC transit card (or plan to buy at KIX)" },
    ],
  },
  {
    id: "electronics",
    label: "Electronics",
    items: [
      { text: "Phone + charger" },
      { text: "Portable battery pack (15,000+ mAh for 15k steps/day)" },
      { text: "Japan adapter NOT needed (Japan Type A = US plugs)" },
      { text: "Camera" },
      { text: "Earbuds/headphones" },
    ],
  },
  {
    id: "apps",
    label: "Apps (pre-install)",
    items: [
      { text: "Google Maps (download Japan offline maps)" },
      { text: "Google Translate (download Japanese language pack)" },
      { text: "Hyperdia or Google Maps for train times" },
      { text: "IC card app (Suica or ICOCA)" },
    ],
  },
  {
    id: "clothing",
    label: "Clothing (March = 8-18°C, layers!)",
    items: [
      { text: "Comfortable walking shoes (expect 15,000+ steps/day)" },
      { text: "Backup walking shoes (second pair essential)" },
      { text: "Light jacket / windbreaker" },
      { text: "Layers (sweater/fleece for Kanazawa & evenings)" },
      { text: "Comfortable socks (removing shoes at temples)" },
    ],
  },
  {
    id: "health",
    label: "Health & Comfort",
    items: [
      { text: "Any prescription medications" },
      { text: "Blister prevention / foot care" },
      { text: "Sunscreen" },
      { text: "Portable umbrella (spring showers)" },
      { text: "Small day backpack for city exploring" },
    ],
  },
  {
    id: "japan",
    label: "Japan-Specific",
    items: [
      { text: "Small towel (not always provided at temples/parks)" },
      { text: "Yen coins / small bills for vending machines" },
      { text: "Pocket WiFi or SIM card sorted (KIX airport pickup)" },
    ],
  },
];

const STORAGE_KEY = "shogun_checklist_v1";

function loadChecked(): Record<string, boolean> {
  if (typeof window === "undefined") return {};
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveChecked(checked: Record<string, boolean>) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(checked));
  } catch {
    // localStorage not available — ignore
  }
}

const ALL_ITEMS = CATEGORIES.flatMap((c) => c.items);

export default function ChecklistPage() {
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [openCategories, setOpenCategories] = useState<Record<string, boolean>>(
    Object.fromEntries(CATEGORIES.map((c) => [c.id, true]))
  );
  const [confirmReset, setConfirmReset] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setChecked(loadChecked());
    setMounted(true);
  }, []);

  function toggle(text: string) {
    const next = { ...checked, [text]: !checked[text] };
    setChecked(next);
    saveChecked(next);
  }

  function toggleCategory(id: string) {
    setOpenCategories((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  function handleReset() {
    if (!confirmReset) {
      setConfirmReset(true);
      return;
    }
    setChecked({});
    saveChecked({});
    setConfirmReset(false);
  }

  const totalItems = ALL_ITEMS.length;
  const checkedCount = ALL_ITEMS.filter((item) => checked[item.text]).length;
  const pct = totalItems > 0 ? Math.round((checkedCount / totalItems) * 100) : 0;

  return (
    <div style={{ padding: "1.5rem", maxWidth: "700px" }}>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 900, marginBottom: "0.25rem" }}>
        Packing Checklist
      </h1>
      <p style={{ fontSize: "0.85rem", color: "#6b7280", marginBottom: "1rem" }}>
        Pre-departure checklist. State saved in your browser.
      </p>

      {/* Progress bar */}
      <div style={{
        background: "white",
        borderRadius: "12px",
        padding: "1rem",
        boxShadow: "0 1px 3px rgba(0,0,0,0.07)",
        marginBottom: "1rem",
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
          <span style={{ fontWeight: 700, fontSize: "0.95rem" }}>
            {mounted ? `${checkedCount} of ${totalItems} packed` : `0 of ${totalItems} packed`}
          </span>
          <span style={{ fontSize: "0.85rem", color: "#6b7280" }}>
            {mounted ? `${pct}%` : "0%"}
          </span>
        </div>
        <div style={{ height: "8px", background: "#e2e8f0", borderRadius: "999px", overflow: "hidden" }}>
          <div style={{
            height: "100%",
            width: mounted ? `${pct}%` : "0%",
            background: pct === 100 ? "#22c55e" : "#3b82f6",
            borderRadius: "999px",
            transition: "width 0.3s ease",
          }} />
        </div>
        <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.5rem" }}>
          <button
            onClick={handleReset}
            style={{
              padding: "0.35rem 0.9rem",
              borderRadius: "6px",
              border: "1px solid",
              borderColor: confirmReset ? "#ef4444" : "#e2e8f0",
              background: confirmReset ? "#fee2e2" : "white",
              color: confirmReset ? "#991b1b" : "#374151",
              fontSize: "0.8rem",
              cursor: "pointer",
            }}
          >
            {confirmReset ? "Confirm reset?" : "Reset all"}
          </button>
          {confirmReset && (
            <button
              onClick={() => setConfirmReset(false)}
              style={{
                padding: "0.35rem 0.9rem",
                borderRadius: "6px",
                border: "1px solid #e2e8f0",
                background: "white",
                color: "#374151",
                fontSize: "0.8rem",
                cursor: "pointer",
              }}
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* Categories */}
      <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
        {CATEGORIES.map((cat) => {
          const isOpen = openCategories[cat.id];
          const catChecked = cat.items.filter((item) => mounted && checked[item.text]).length;
          return (
            <div key={cat.id} style={{
              background: "white",
              borderRadius: "12px",
              boxShadow: "0 1px 3px rgba(0,0,0,0.07)",
              overflow: "hidden",
              border: "1px solid #f1f5f9",
            }}>
              <button
                onClick={() => toggleCategory(cat.id)}
                style={{
                  width: "100%",
                  display: "flex",
                  alignItems: "center",
                  padding: "0.85rem 1rem",
                  background: "white",
                  border: "none",
                  cursor: "pointer",
                  textAlign: "left",
                  gap: "0.5rem",
                }}
              >
                <span style={{ fontWeight: 700, fontSize: "0.9rem", color: "#111827", flex: 1 }}>
                  {cat.label}
                </span>
                <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                  {mounted ? `${catChecked}/${cat.items.length}` : `0/${cat.items.length}`}
                </span>
                <span style={{ color: "#94a3b8", fontSize: "0.8rem" }}>
                  {isOpen ? "▲" : "▼"}
                </span>
              </button>
              {isOpen && (
                <div style={{ borderTop: "1px solid #f1f5f9" }}>
                  {cat.items.map((item) => {
                    const isChecked = mounted && !!checked[item.text];
                    return (
                      <div
                        key={item.text}
                        onClick={() => toggle(item.text)}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "0.75rem",
                          padding: "0.65rem 1rem",
                          cursor: "pointer",
                          background: isChecked ? "#f0fdf4" : "white",
                          borderBottom: "1px solid #f8fafc",
                          transition: "background 0.1s",
                          userSelect: "none",
                        }}
                      >
                        <div style={{
                          width: "18px",
                          height: "18px",
                          borderRadius: "4px",
                          border: isChecked ? "none" : "2px solid #cbd5e1",
                          background: isChecked ? "#22c55e" : "white",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          flexShrink: 0,
                          transition: "all 0.15s",
                        }}>
                          {isChecked && <span style={{ color: "white", fontSize: "0.7rem", fontWeight: 900 }}>✓</span>}
                        </div>
                        <span style={{
                          fontSize: "0.875rem",
                          color: isChecked ? "#6b7280" : "#111827",
                          textDecoration: isChecked ? "line-through" : "none",
                        }}>
                          {item.text}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
