import type { ChatMessage as ChatMsg } from "@/lib/types";

interface Props {
  message: ChatMsg;
}

export default function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";
  return (
    <div style={{
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start",
      marginBottom: "0.75rem",
    }}>
      <div style={{
        maxWidth: "75%",
        padding: "0.625rem 0.875rem",
        borderRadius: isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
        background: isUser ? "var(--city-accent)" : "white",
        color: isUser ? "white" : "#111827",
        fontSize: "0.9rem",
        lineHeight: 1.5,
        boxShadow: "0 1px 2px rgba(0,0,0,0.06)",
        whiteSpace: "pre-wrap",
      }}>
        {message.content}
      </div>
    </div>
  );
}
