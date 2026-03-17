"use client";

import { useState } from "react";

interface Section {
  id: string;
  icon: string;
  title: string;
  content: React.ReactNode;
}

const SECTIONS: Section[] = [
  {
    id: "overview",
    icon: "🚆",
    title: "IC Cards Overview",
    content: (
      <div>
        <p style={{ marginBottom: "0.75rem" }}>
          <strong>ICOCA</strong> (Kansai) and <strong>Suica</strong> (Tokyo/Kanto) both work everywhere in Japan — at JR stations, subway lines, buses, and even many convenience stores and vending machines.
        </p>
        <p>
          Get either one. They are fully interoperable across Japan. No need to buy both.
        </p>
      </div>
    ),
  },
  {
    id: "buy",
    icon: "🎫",
    title: "Where to Buy",
    content: (
      <div>
        <ul style={{ paddingLeft: "1.25rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <li>Any JR station vending machine or ticket window</li>
          <li>
            <strong>At KIX airport (where we arrive):</strong> Buy at the JR West counter near the arrivals exit — easiest first stop after landing
          </li>
          <li>Initial cost: card face value + ¥500 deposit (refundable when you return the card)</li>
          <li>Load ¥3,000–5,000 to start — enough for first 1–2 days</li>
        </ul>
      </div>
    ),
  },
  {
    id: "howto",
    icon: "💳",
    title: "How to Use",
    content: (
      <div>
        <ul style={{ paddingLeft: "1.25rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <li>Tap the IC card on the <strong>yellow card readers</strong> when entering and exiting a station — both in and out</li>
          <li>The reader displays your current balance after each tap</li>
          <li>Top up at any green vending machine (IC/Suica machines) at any JR or metro station</li>
          <li>You can also top up via the Suica or ICOCA smartphone app if you set it up</li>
          <li>The card works at most convenience stores (7-Eleven, Lawson, FamilyMart), vending machines, and taxis in Tokyo</li>
        </ul>
      </div>
    ),
  },
  {
    id: "coverage",
    icon: "🗺️",
    title: "Our Trip Coverage",
    content: (
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {[
          {
            city: "Osaka",
            color: "#f59e0b",
            details: "JR, Osaka Metro, Kintetsu (to Nara), Hankyu, Hanshin — all accept IC cards. One card covers everything.",
          },
          {
            city: "Nara",
            color: "#22c55e",
            details: "Kintetsu from Osaka Namba (~45 min, ~¥680). JR Yamatoji line from Osaka also works. Both accept IC cards.",
          },
          {
            city: "Kanazawa",
            color: "#3b82f6",
            details: "Hokuriku Shinkansen from Osaka (~2h, reserved seat — purchase separately). IC card works on local Kanazawa buses and city trams.",
          },
          {
            city: "Tokyo",
            color: "#8b5cf6",
            details: "All JR lines, Tokyo Metro, Toei subway — IC card works everywhere. Suica also accepted on most Tokyo taxis.",
          },
        ].map((item) => (
          <div key={item.city} style={{
            borderLeft: `3px solid ${item.color}`,
            paddingLeft: "0.75rem",
          }}>
            <div style={{ fontWeight: 700, marginBottom: "0.2rem" }}>{item.city}</div>
            <div style={{ fontSize: "0.875rem", color: "#4b5563" }}>{item.details}</div>
          </div>
        ))}
      </div>
    ),
  },
  {
    id: "tips",
    icon: "💡",
    title: "Key Tips",
    content: (
      <div>
        <ul style={{ paddingLeft: "1.25rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <li>Keep <strong>¥2,000+</strong> balance at all times — don't let it run empty on a busy transit day</li>
          <li>At end of trip: refund remaining balance at any JR station (minus ¥220 handling fee + ¥500 deposit back)</li>
          <li><strong>Shinkansen reserved seats must be purchased separately</strong> — IC card only covers local/rapid trains, not the bullet train itself</li>
          <li>Kintetsu to Nara: IC cards work on Kintetsu IC-compatible trains — just tap in/out as normal</li>
          <li>If you get an "insufficient balance" gate beep — use the fare adjustment machine (精算機) inside the gate before exiting</li>
        </ul>
      </div>
    ),
  },
];

export default function TransitPage() {
  const [openSection, setOpenSection] = useState<string | null>("overview");

  return (
    <div style={{ padding: "1.5rem", maxWidth: "800px" }}>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 900, marginBottom: "0.25rem" }}>
        Transit Guide
      </h1>
      <p style={{ fontSize: "0.85rem", color: "#6b7280", marginBottom: "1.5rem" }}>
        Getting around Japan with IC cards — everything you need to know.
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
        {SECTIONS.map((section) => {
          const isOpen = openSection === section.id;
          return (
            <div key={section.id} style={{
              background: "white",
              borderRadius: "12px",
              boxShadow: "0 1px 3px rgba(0,0,0,0.07)",
              overflow: "hidden",
              border: isOpen ? "1px solid #bfdbfe" : "1px solid #f1f5f9",
            }}>
              <button
                onClick={() => setOpenSection(isOpen ? null : section.id)}
                style={{
                  width: "100%",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.75rem",
                  padding: "0.9rem 1rem",
                  background: isOpen ? "#eff6ff" : "white",
                  border: "none",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "background 0.15s",
                }}
              >
                <span style={{ fontSize: "1.25rem" }}>{section.icon}</span>
                <span style={{ fontWeight: 700, fontSize: "0.95rem", color: "#111827", flex: 1 }}>
                  {section.title}
                </span>
                <span style={{ color: "#94a3b8", fontSize: "0.9rem" }}>
                  {isOpen ? "▲" : "▼"}
                </span>
              </button>
              {isOpen && (
                <div style={{ padding: "0 1rem 1rem 1rem", fontSize: "0.875rem", color: "#374151", lineHeight: 1.6 }}>
                  {section.content}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
