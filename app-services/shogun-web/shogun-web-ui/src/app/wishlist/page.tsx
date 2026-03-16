"use client";

import { useEffect, useState, useRef } from "react";
import { api } from "@/lib/api";
import type { WishlistItem } from "@/lib/types";
import { CITIES } from "@/lib/cities";

const CITY_OPTIONS = ["", ...Object.keys(CITIES)];

interface Toast {
  msg: string;
  type: "success" | "error";
}

export default function WishlistPage() {
  const [items, setItems] = useState<WishlistItem[]>([]);
  const [city, setCity] = useState("");
  const [desc, setDesc] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [note, setNote] = useState<Record<number, string>>({});
  const [toast, setToast] = useState<Toast | null>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  function showToast(msg: string, type: "success" | "error") {
    if (toastTimer.current) clearTimeout(toastTimer.current);
    setToast({ msg, type });
    if (type === "success") {
      toastTimer.current = setTimeout(() => setToast(null), 3000);
    }
  }

  function dismissToast() {
    if (toastTimer.current) clearTimeout(toastTimer.current);
    setToast(null);
  }

  function load() {
    api.wishlist.list().then((d) => setItems(d as WishlistItem[]));
  }

  useEffect(() => { load(); }, []);

  async function submit() {
    if (!desc.trim()) return;
    setSubmitting(true);
    const savedDesc = desc.trim();
    const savedCity = city;
    try {
      await api.wishlist.create({ city: city || undefined, description: savedDesc });
      setDesc("");
      setCity("");
      load();
      const cityLabel = savedCity ? ` your ${savedCity}` : "";
      showToast(`Saved! '${savedDesc}' added to${cityLabel} wishlist.`, "success");
    } catch (e) {
      console.error("Wishlist submit failed:", e);
      showToast("Save failed — please try again.", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function approve(id: number) {
    await api.wishlist.approve(id, note[id]);
    load();
  }

  async function reject(id: number) {
    await api.wishlist.reject(id);
    load();
  }

  const pending = items.filter((i) => i.status === "pending");
  const decided = items.filter((i) => i.status !== "pending");

  return (
    <div style={{ padding: "1.5rem", maxWidth: "760px" }}>
      <h1 style={{ fontSize: "1.4rem", fontWeight: 900, marginBottom: "1.25rem" }}>⭐ Wishlist</h1>

      {/* Submission form */}
      <div style={{ background: "white", borderRadius: "12px", padding: "1.25rem", boxShadow: "0 1px 3px rgba(0,0,0,0.07)", marginBottom: "1.5rem" }}>
        <h2 style={{ fontWeight: 700, fontSize: "0.95rem", marginBottom: "0.75rem" }}>Submit a wish</h2>
        <select value={city} onChange={(e) => setCity(e.target.value)}
          style={{ width: "100%", marginBottom: "0.5rem", padding: "0.5rem", borderRadius: "6px", border: "1px solid #e5e7eb", fontSize: "0.875rem" }}>
          <option value="">Any city</option>
          {Object.values(CITIES).map((c) => (
            <option key={c.slug} value={c.slug}>{c.name}</option>
          ))}
        </select>
        <textarea
          value={desc}
          onChange={(e) => setDesc(e.target.value)}
          placeholder="What do you want to do or see?"
          rows={3}
          style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #e5e7eb", fontSize: "0.875rem", resize: "vertical" }}
        />
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginTop: "0.625rem" }}>
          <button onClick={submit} disabled={!desc.trim() || submitting}
            style={{ padding: "0.5rem 1.25rem", background: "var(--city-accent)", color: "white",
              border: "none", borderRadius: "8px", fontWeight: 700, cursor: "pointer",
              opacity: !desc.trim() || submitting ? 0.5 : 1 }}>
            {submitting ? "Saving…" : "Submit"}
          </button>
          <span style={{ fontSize: "0.75rem", color: "#9ca3af", lineHeight: 1.4 }}>
            Your wishlist items are saved for planning. The AI research pipeline will process them pre-trip.
          </span>
        </div>
      </div>

      {/* Pending queue (admin) */}
      {pending.length > 0 && (
        <div style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ fontWeight: 700, marginBottom: "0.75rem" }}>Pending ({pending.length})</h2>
          {pending.map((item) => (
            <div key={item.id} style={{ background: "white", borderRadius: "10px", padding: "1rem",
              boxShadow: "0 1px 3px rgba(0,0,0,0.06)", marginBottom: "0.75rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.375rem" }}>
                <span className="status-pending" style={{ padding: "2px 8px", borderRadius: "9999px", fontSize: "0.75rem" }}>Pending</span>
                {item.city && <span style={{ fontSize: "0.75rem", color: "#6b7280" }}>{item.city}</span>}
              </div>
              <p style={{ fontSize: "0.9rem", marginBottom: "0.625rem" }}>{item.description}</p>
              <input
                placeholder="Itinerary note (optional)"
                value={note[item.id] ?? ""}
                onChange={(e) => setNote((n) => ({ ...n, [item.id]: e.target.value }))}
                style={{ width: "100%", padding: "0.375rem 0.5rem", borderRadius: "6px", border: "1px solid #e5e7eb",
                  fontSize: "0.8rem", marginBottom: "0.5rem" }}
              />
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button onClick={() => approve(item.id)}
                  style={{ padding: "0.375rem 0.875rem", background: "#10b981", color: "white", border: "none",
                    borderRadius: "6px", fontSize: "0.8rem", fontWeight: 600, cursor: "pointer" }}>
                  Approve
                </button>
                <button onClick={() => reject(item.id)}
                  style={{ padding: "0.375rem 0.875rem", background: "#ef4444", color: "white", border: "none",
                    borderRadius: "6px", fontSize: "0.8rem", fontWeight: 600, cursor: "pointer" }}>
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Decided */}
      {decided.length > 0 && (
        <div>
          <h2 style={{ fontWeight: 700, marginBottom: "0.75rem", color: "#6b7280" }}>Archive</h2>
          {decided.map((item) => (
            <div key={item.id} style={{ background: "#f8fafc", borderRadius: "10px", padding: "0.875rem",
              marginBottom: "0.5rem", opacity: 0.8 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.25rem" }}>
                <span className={`status-${item.status}`} style={{ padding: "2px 8px", borderRadius: "9999px", fontSize: "0.75rem" }}>
                  {item.status}
                </span>
                {item.city && <span style={{ fontSize: "0.75rem", color: "#9ca3af" }}>{item.city}</span>}
              </div>
              <p style={{ fontSize: "0.875rem", color: "#4b5563" }}>{item.description}</p>
              {item.itinerary_note && (
                <p style={{ fontSize: "0.8rem", color: "#6b7280", marginTop: "0.25rem" }}>📝 {item.itinerary_note}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Toast notification */}
      {toast && (
        <div
          onClick={toast.type === "error" ? dismissToast : undefined}
          style={{
            position: "fixed",
            bottom: "1.5rem",
            right: "1.5rem",
            zIndex: 9999,
            padding: "0.875rem 1.25rem",
            borderRadius: "10px",
            boxShadow: "0 4px 16px rgba(0,0,0,0.15)",
            background: toast.type === "success" ? "#d1fae5" : "#fee2e2",
            color: toast.type === "success" ? "#065f46" : "#991b1b",
            fontSize: "0.875rem",
            fontWeight: 600,
            maxWidth: "320px",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            cursor: toast.type === "error" ? "pointer" : "default",
          }}
        >
          <span>{toast.type === "success" ? "✓" : "✕"}</span>
          <span>{toast.msg}</span>
          {toast.type === "error" && (
            <span style={{ marginLeft: "auto", fontSize: "0.75rem", opacity: 0.7 }}>tap to dismiss</span>
          )}
        </div>
      )}
    </div>
  );
}
