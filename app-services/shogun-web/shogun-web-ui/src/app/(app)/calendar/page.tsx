import { api } from "@/lib/api";
import type { ItineraryLeg } from "@/lib/types";
import CalendarGrid from "@/components/calendar/CalendarGrid";

// Force server-side rendering on every request so leg data is always current
export const dynamic = "force-dynamic";

async function getLegs(): Promise<ItineraryLeg[]> {
  try {
    return await api.calendar.list() as ItineraryLeg[];
  } catch {
    return [];
  }
}

export default async function CalendarPage() {
  const legs = await getLegs();

  return (
    <div>
      <div style={{ padding: "1.25rem 1rem 0" }}>
        <h1 style={{ fontSize: "1.4rem", fontWeight: 900 }}>Trip Calendar</h1>
        <p style={{ color: "#6b7280", fontSize: "0.85rem", marginTop: "0.25rem" }}>
          Mar 23 – Apr 9, 2026 · Click any day for details
        </p>
      </div>
      <CalendarGrid legs={legs} />
    </div>
  );
}
