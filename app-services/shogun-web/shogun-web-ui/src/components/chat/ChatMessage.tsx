import type { ChatMessage as ChatMsg } from "@/lib/types";

interface Props {
  message: ChatMsg;
}

export default function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";
  const toolActions = (!isUser && message.tool_actions && message.tool_actions.length > 0)
    ? message.tool_actions
    : null;

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: isUser ? "flex-end" : "flex-start",
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

      {/* Tool action badges — shown only on AI messages that used tools */}
      {toolActions && (
        <div style={{
          maxWidth: "75%",
          marginTop: "0.25rem",
          display: "flex",
          flexDirection: "column",
          gap: "0.2rem",
        }}>
          {toolActions.map((action, idx) => (
            <div key={idx} style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.3rem",
              padding: "2px 8px",
              background: "#f0fdf4",
              border: "1px solid #bbf7d0",
              borderRadius: "6px",
              fontSize: "0.72rem",
              color: "#166534",
            }}>
              <span style={{ fontWeight: 600 }}>✓</span>
              <span>{action.summary}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
