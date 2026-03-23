import Link from "next/link";
import type { ItineraryLeg } from "@/lib/types";

const LEG_TYPE_LABELS: Record<string, string> = {
  flight:     "Flight",
  hotel:      "Hotel",
  activity:   "Activity",
  transit:    "Transit",
  restaurant: "Restaurant",
};

interface Props {
  leg: ItineraryLeg;
  compact?: boolean;
}

export default function LegCard({ leg, compact }: Props) {
  const typeLabel = LEG_TYPE_LABELS[leg.leg_type] ?? leg.leg_type;
  const isTbd = !leg.date_start;
  const hasGuide = !!leg.trip_poi_id;

  const titleContent = (
    <span style={{ fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", display: "block" }}>
      {typeLabel} · {leg.title}
      {hasGuide && <span style={{ marginLeft: "0.35rem", fontSize: "0.7rem", color: "var(--city-accent, #1d4ed8)" }}>Guide &rarr;</span>}
    </span>
  );

  return (
    <div className={`leg-${isTbd ? "tbd" : leg.leg_type}`}
      style={{
        borderRadius: "6px",
        padding: compact ? "4px 8px" : "0.625rem 0.875rem",
        marginBottom: compact ? "2px" : "0.5rem",
        fontSize: compact ? "0.75rem" : "0.875rem",
      }}
    >
      {hasGuide ? (
        <Link href={`/pois/${leg.trip_poi_id}`} style={{ textDecoration: "none", color: "inherit" }}>
          {titleContent}
        </Link>
      ) : (
        titleContent
      )}
      {!compact && leg.description && (
        <div style={{ marginTop: "0.25rem", fontSize: "0.8rem", opacity: 0.75, lineHeight: 1.4 }}>
          {leg.description}
        </div>
      )}
      {!compact && leg.notes && (
        <div style={{ marginTop: "0.375rem", fontSize: "0.8rem", background: "#fef9c3", borderRadius: 4, padding: "4px 8px", color: "#92400e" }}>
          {leg.notes}
        </div>
      )}
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
          {leg.address_ja}
        </div>
      )}
    </div>
  );
}
