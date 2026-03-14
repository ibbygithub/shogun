import type { Reminder } from "@/lib/types";

interface Props {
  reminder: Reminder;
}

export default function DayReminder({ reminder }: Props) {
  return (
    <div className={`reminder-${reminder.type}`}
      style={{
        display: "flex",
        gap: "0.625rem",
        padding: "0.625rem 0.75rem",
        borderRadius: "6px",
        marginBottom: "0.375rem",
        alignItems: "flex-start",
        fontSize: "0.85rem",
      }}
    >
      <span style={{ fontSize: "1rem", flexShrink: 0 }}>{reminder.icon}</span>
      <span style={{ lineHeight: 1.4 }}>{reminder.text}</span>
    </div>
  );
}
