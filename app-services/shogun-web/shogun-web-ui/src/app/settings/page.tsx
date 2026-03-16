"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const [prefs, setPrefs] = useState<Record<string, string>>({});
  const [users, setUsers] = useState<any[]>([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.settings.preferences().then((p) => setPrefs(p as Record<string, string>));
    api.settings.users().then((u) => setUsers(u as any[])).catch(() => {});
  }, []);

  async function savePref(type: string, value: string) {
    setSaving(true);
    try {
      await api.settings.setPreference(type, value);
      setPrefs((p) => ({ ...p, [type]: value }));
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  }

  const dietaryTypes = ["dietary_restrictions", "food_likes", "food_dislikes", "allergies"];

  return (
    <div style={{ padding: "1.5rem", maxWidth: "640px" }}>
      <h1 style={{ fontSize: "1.4rem", fontWeight: 900, marginBottom: "1.5rem" }}>⚙️ Settings</h1>

      {/* Dietary preferences */}
      <div style={{ background: "white", borderRadius: "12px", padding: "1.25rem", boxShadow: "0 1px 3px rgba(0,0,0,0.07)", marginBottom: "1.25rem" }}>
        <h2 style={{ fontWeight: 700, marginBottom: "1rem" }}>Food Preferences</h2>
        {dietaryTypes.map((type) => (
          <div key={type} style={{ marginBottom: "0.875rem" }}>
            <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "#374151", display: "block", marginBottom: "0.25rem", textTransform: "capitalize" }}>
              {type.replace(/_/g, " ")}
            </label>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <input
                defaultValue={prefs[type] ?? ""}
                onBlur={(e) => {
                  if (e.target.value !== (prefs[type] ?? "")) {
                    savePref(type, e.target.value);
                  }
                }}
                style={{ flex: 1, padding: "0.5rem", borderRadius: "6px", border: "1px solid #e5e7eb", fontSize: "0.875rem" }}
              />
            </div>
          </div>
        ))}
        {saved && <div style={{ color: "#10b981", fontSize: "0.8rem" }}>✓ Saved</div>}
      </div>

      {/* User management (admin only) */}
      {users.length > 0 && (
        <div style={{ background: "white", borderRadius: "12px", padding: "1.25rem", boxShadow: "0 1px 3px rgba(0,0,0,0.07)" }}>
          <h2 style={{ fontWeight: 700, marginBottom: "0.75rem" }}>Users</h2>
          <table style={{ width: "100%", fontSize: "0.875rem", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #e5e7eb" }}>
                <th style={{ textAlign: "left", padding: "0.375rem 0", color: "#6b7280", fontWeight: 600 }}>Name</th>
                <th style={{ textAlign: "left", padding: "0.375rem 0", color: "#6b7280", fontWeight: 600 }}>Email</th>
                <th style={{ textAlign: "left", padding: "0.375rem 0", color: "#6b7280", fontWeight: 600 }}>Role</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} style={{ borderBottom: "1px solid #f1f5f9" }}>
                  <td style={{ padding: "0.5rem 0" }}>{u.name}</td>
                  <td style={{ padding: "0.5rem 0", color: "#6b7280" }}>{u.email}</td>
                  <td style={{ padding: "0.5rem 0" }}>
                    <span style={{ background: "#eff6ff", color: "#1d4ed8", padding: "2px 8px", borderRadius: "9999px", fontSize: "0.75rem" }}>
                      {u.role}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
