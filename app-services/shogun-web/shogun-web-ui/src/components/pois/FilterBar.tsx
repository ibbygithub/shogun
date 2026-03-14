"use client";

const CATEGORIES = ["temple", "food", "anime", "camera", "activity", "market", "garden", "shrine"];

interface Props {
  active: string[];
  onChange: (tags: string[]) => void;
}

export default function FilterBar({ active, onChange }: Props) {
  function toggle(tag: string) {
    if (active.includes(tag)) {
      onChange(active.filter((t) => t !== tag));
    } else {
      onChange([...active, tag]);
    }
  }

  return (
    <div style={{ display: "flex", gap: "0.375rem", flexWrap: "wrap", padding: "0.75rem 1rem" }}>
      {CATEGORIES.map((cat) => {
        const on = active.includes(cat);
        return (
          <button key={cat} onClick={() => toggle(cat)}
            style={{
              padding: "4px 12px",
              borderRadius: "9999px",
              border: "1px solid",
              borderColor: on ? "var(--city-accent)" : "#d1d5db",
              background: on ? "var(--city-accent)" : "white",
              color: on ? "white" : "#374151",
              fontSize: "0.8rem",
              cursor: "pointer",
              fontWeight: on ? 600 : 400,
              transition: "all 0.15s",
            }}
          >
            {cat}
          </button>
        );
      })}
      {active.length > 0 && (
        <button onClick={() => onChange([])}
          style={{ padding: "4px 12px", borderRadius: "9999px", border: "1px solid #ef4444",
            background: "white", color: "#ef4444", fontSize: "0.8rem", cursor: "pointer" }}
        >
          Clear
        </button>
      )}
    </div>
  );
}
