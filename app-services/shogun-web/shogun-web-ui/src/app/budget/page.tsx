"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import type { BudgetItem } from "@/lib/types";

const JPY_TO_USD = 1 / 150;

const CATEGORIES = [
  { value: "food",          label: "Food",          emoji: "🍜" },
  { value: "transport",     label: "Transport",     emoji: "🚆" },
  { value: "accommodation", label: "Accommodation", emoji: "🏨" },
  { value: "activity",      label: "Activity",      emoji: "🎯" },
  { value: "shopping",      label: "Shopping",      emoji: "🛍️" },
  { value: "other",         label: "Other",         emoji: "💴" },
];

function categoryEmoji(cat: string): string {
  return CATEGORIES.find((c) => c.value === cat)?.emoji ?? "💴";
}

function fmtJpy(n: number): string {
  return `¥${n.toLocaleString()}`;
}

function fmtUsd(jpy: number): string {
  return `$${(jpy * JPY_TO_USD).toFixed(0)}`;
}

interface BudgetData {
  items: BudgetItem[];
  total_jpy: number;
  by_category: Record<string, number>;
}

export default function BudgetPage() {
  const [data, setData] = useState<BudgetData | null>(null);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState<string | null>(null);

  // Add form state
  const [formDate, setFormDate] = useState("");
  const [formCategory, setFormCategory] = useState("food");
  const [formDesc, setFormDesc] = useState("");
  const [formAmount, setFormAmount] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.budget.list();
      setData(result);
      setApiError(null);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      // Budget API may not be live yet — show graceful state
      if (msg.includes("404") || msg.includes("Failed to fetch")) {
        setApiError("Budget tracker not yet available — the API endpoint is being set up.");
      } else {
        setApiError("Could not load budget data. Will retry on refresh.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const amount = parseInt(formAmount, 10);
    if (!formDesc.trim() || isNaN(amount) || amount <= 0) {
      setFormError("Description and a valid ¥ amount are required.");
      return;
    }
    setSubmitting(true);
    setFormError(null);
    try {
      await api.budget.add({
        trip_date: formDate || undefined,
        category: formCategory,
        description: formDesc.trim(),
        amount_jpy: amount,
      });
      setFormDesc("");
      setFormAmount("");
      setFormDate("");
      await fetchData();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setFormError(`Failed to add expense: ${msg}`);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    try {
      await api.budget.remove(id);
      await fetchData();
    } catch {
      // Non-critical — refresh will show correct state
    }
  }

  // Group items by date for display
  const itemsByDate: Record<string, BudgetItem[]> = {};
  if (data?.items) {
    for (const item of data.items) {
      const key = item.trip_date ?? "Unspecified";
      if (!itemsByDate[key]) itemsByDate[key] = [];
      itemsByDate[key].push(item);
    }
  }

  const sortedDates = Object.keys(itemsByDate).sort();
  const totalJpy = data?.total_jpy ?? 0;
  const byCategory = data?.by_category ?? {};

  return (
    <div style={{ padding: "1.5rem", maxWidth: "800px" }}>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 900, marginBottom: "0.25rem" }}>
        Budget Tracker
      </h1>
      <p style={{ fontSize: "0.85rem", color: "#6b7280", marginBottom: "1.25rem" }}>
        Track trip expenses in yen. USD shown at ¥150/$ estimate.
      </p>

      {/* API unavailable warning */}
      {apiError && (
        <div style={{
          padding: "0.85rem 1rem",
          background: "#fff7ed",
          borderRadius: "10px",
          border: "1px solid #fed7aa",
          color: "#9a3412",
          fontSize: "0.85rem",
          marginBottom: "1rem",
        }}>
          {apiError}
        </div>
      )}

      {/* Total spent card */}
      <div style={{
        background: "white",
        borderRadius: "12px",
        padding: "1.25rem",
        boxShadow: "0 1px 3px rgba(0,0,0,0.07)",
        marginBottom: "1rem",
      }}>
        <div style={{ fontSize: "0.7rem", color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "0.35rem" }}>
          Total Spent
        </div>
        <div style={{ fontSize: "2.5rem", fontWeight: 900, lineHeight: 1, color: "#111827" }}>
          {loading ? "…" : fmtJpy(totalJpy)}
        </div>
        {!loading && totalJpy > 0 && (
          <div style={{ fontSize: "1rem", color: "#6b7280", marginTop: "0.25rem" }}>
            ≈ {fmtUsd(totalJpy)}
          </div>
        )}
      </div>

      {/* Category breakdown bar chart */}
      {!loading && !apiError && totalJpy > 0 && (
        <div style={{
          background: "white",
          borderRadius: "12px",
          padding: "1rem",
          boxShadow: "0 1px 3px rgba(0,0,0,0.07)",
          marginBottom: "1rem",
        }}>
          <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#374151", marginBottom: "0.75rem" }}>
            By Category
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {CATEGORIES.filter((cat) => byCategory[cat.value] > 0).map((cat) => {
              const amount = byCategory[cat.value] ?? 0;
              const pct = totalJpy > 0 ? (amount / totalJpy) * 100 : 0;
              return (
                <div key={cat.value}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem", marginBottom: "0.2rem" }}>
                    <span>{cat.emoji} {cat.label}</span>
                    <span style={{ color: "#6b7280" }}>{fmtJpy(amount)} ({Math.round(pct)}%)</span>
                  </div>
                  <div style={{ height: "6px", background: "#e2e8f0", borderRadius: "999px", overflow: "hidden" }}>
                    <div style={{
                      height: "100%",
                      width: `${pct}%`,
                      background: "#3b82f6",
                      borderRadius: "999px",
                    }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Add expense form */}
      {!apiError && (
        <div style={{
          background: "white",
          borderRadius: "12px",
          padding: "1rem",
          boxShadow: "0 1px 3px rgba(0,0,0,0.07)",
          marginBottom: "1rem",
        }}>
          <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#374151", marginBottom: "0.75rem" }}>
            Add Expense
          </div>
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.6rem" }}>
              <div>
                <label style={{ fontSize: "0.75rem", color: "#6b7280", display: "block", marginBottom: "0.2rem" }}>
                  Date (optional)
                </label>
                <input
                  type="date"
                  value={formDate}
                  onChange={(e) => setFormDate(e.target.value)}
                  style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #e2e8f0", fontSize: "0.85rem", boxSizing: "border-box" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "0.75rem", color: "#6b7280", display: "block", marginBottom: "0.2rem" }}>
                  Category
                </label>
                <select
                  value={formCategory}
                  onChange={(e) => setFormCategory(e.target.value)}
                  style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #e2e8f0", fontSize: "0.85rem", boxSizing: "border-box" }}
                >
                  {CATEGORIES.map((cat) => (
                    <option key={cat.value} value={cat.value}>
                      {cat.emoji} {cat.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label style={{ fontSize: "0.75rem", color: "#6b7280", display: "block", marginBottom: "0.2rem" }}>
                Description
              </label>
              <input
                type="text"
                value={formDesc}
                onChange={(e) => setFormDesc(e.target.value)}
                placeholder="e.g. Ramen at Ichiran"
                style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #e2e8f0", fontSize: "0.85rem", boxSizing: "border-box" }}
              />
            </div>
            <div>
              <label style={{ fontSize: "0.75rem", color: "#6b7280", display: "block", marginBottom: "0.2rem" }}>
                Amount (¥)
              </label>
              <input
                type="number"
                value={formAmount}
                onChange={(e) => setFormAmount(e.target.value)}
                placeholder="1200"
                min="1"
                style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", border: "1px solid #e2e8f0", fontSize: "0.85rem", boxSizing: "border-box" }}
              />
            </div>
            {formError && (
              <div style={{ fontSize: "0.8rem", color: "#ef4444" }}>{formError}</div>
            )}
            <button
              type="submit"
              disabled={submitting}
              style={{
                padding: "0.6rem 1.25rem",
                background: submitting ? "#94a3b8" : "#3b82f6",
                color: "white",
                border: "none",
                borderRadius: "8px",
                fontWeight: 700,
                fontSize: "0.875rem",
                cursor: submitting ? "default" : "pointer",
                alignSelf: "flex-start",
              }}
            >
              {submitting ? "Adding…" : "Add Expense"}
            </button>
          </form>
        </div>
      )}

      {/* Expense list grouped by date */}
      {!loading && !apiError && sortedDates.length === 0 && (
        <div style={{
          textAlign: "center",
          color: "#94a3b8",
          fontSize: "0.875rem",
          padding: "2rem",
          background: "white",
          borderRadius: "12px",
        }}>
          No expenses yet — add your first one above.
        </div>
      )}

      {sortedDates.map((date) => (
        <div key={date} style={{ marginBottom: "1rem" }}>
          <div style={{
            fontSize: "0.75rem",
            fontWeight: 700,
            color: "#6b7280",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            marginBottom: "0.4rem",
          }}>
            {date === "Unspecified" ? "Unspecified date" : new Date(date + "T12:00:00").toLocaleDateString("en", { weekday: "long", month: "short", day: "numeric" })}
          </div>
          <div style={{
            background: "white",
            borderRadius: "12px",
            boxShadow: "0 1px 3px rgba(0,0,0,0.07)",
            overflow: "hidden",
          }}>
            {itemsByDate[date].map((item, idx) => (
              <div
                key={item.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.75rem",
                  padding: "0.7rem 1rem",
                  borderBottom: idx < itemsByDate[date].length - 1 ? "1px solid #f8fafc" : "none",
                }}
              >
                <span style={{ fontSize: "1.25rem" }}>{categoryEmoji(item.category)}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "#111827" }}>
                    {item.description}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                    {item.category}
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "#111827" }}>
                    {fmtJpy(item.amount_jpy)}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                    {fmtUsd(item.amount_jpy)}
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(item.id)}
                  title="Delete expense"
                  style={{
                    padding: "0.25rem 0.5rem",
                    background: "none",
                    border: "1px solid #e2e8f0",
                    borderRadius: "6px",
                    color: "#94a3b8",
                    cursor: "pointer",
                    fontSize: "0.75rem",
                  }}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
