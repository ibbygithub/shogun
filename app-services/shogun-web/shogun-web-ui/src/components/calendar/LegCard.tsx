import type { ItineraryLeg } from "@/lib/types";

const LEG_TYPE_LABELS: Record<string, string> = {
  flight:     "✈️ Flight",
  hotel:      "🏨 Hotel",
  activity:   "🎯 Activity",
  transit:    "🚃 Transit",
  restaurant: "🍜 Restaurant",
};

interface Props {
  leg: ItineraryLeg;
  compact?: boolean;
}

export default function LegCard({ leg, compact }: Props) {
  const typeLabel = LEG_TYPE_LABELS[leg.leg_type] ?? leg.leg_type;
  const isTbd = !leg.date_start;

  return (
    <div className={`leg-${isTbd ? "tbd" : leg.leg_type}`}
      style={{
        borderRadius: "6px",
        padding: compact ? "4px 8px" : "0.625rem 0.875rem",
        marginBottom: compact ? "2px" : "0.5rem",
        fontSize: compact ? "0.75rem" : "0.875rem",
      }}
    >
      <div style={{ fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
        {typeLabel} · {leg.title}
      </div>
      {!compact && leg.address_en && (
        <div style={{ marginTop: "0.25rem", fontSize: "0.8rem", opacity: 0.75 }}>
          {leg.address_en}
        </div>
      )}
      {!compact && leg.address_ja && (
        <div style={{ fontSize: "0.75rem", opacity: 0.6, cursor: "pointer" }}
          onClick={() => navigator.clipboard?.writeText(leg.address_ja!)}
          title="Click to copy Japanese address"
        >
          {leg.address_ja} 📋
        </div>
      )}
    </div>
  );
}
