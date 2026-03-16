"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { RemindersResponse } from "@/lib/types";
import DayReminder from "./DayReminder";

interface Props {
  date?: string; // YYYY-MM-DD — omit for global only
  showGlobal?: boolean;
}

export default function RemindersPanel({ date, showGlobal = true }: Props) {
  const [data, setData] = useState<RemindersResponse | null>(null);

  useEffect(() => {
    api.reminders.get(date).then((d) => setData(d as RemindersResponse));
  }, [date]);

  if (!data) return null;

  const hasDate = data.date_reminders.length > 0;
  const hasGlobal = showGlobal && data.global_reminders.length > 0;

  if (!hasDate && !hasGlobal) return null;

  return (
    <div>
      {hasDate && (
        <div style={{ marginBottom: "0.75rem" }}>
          <div style={{ fontWeight: 700, fontSize: "0.8rem", color: "#374151", marginBottom: "0.375rem", textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Today's logistics
          </div>
          {data.date_reminders.map((r, i) => <DayReminder key={i} reminder={r} />)}
        </div>
      )}
      {hasGlobal && (
        <div>
          <div style={{ fontWeight: 700, fontSize: "0.8rem", color: "#374151", marginBottom: "0.375rem", textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Japan tips
          </div>
          {data.global_reminders.map((r, i) => <DayReminder key={i} reminder={r} />)}
        </div>
      )}
    </div>
  );
}
