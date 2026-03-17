import type { ChatMessage as ChatMsg } from "@/lib/types";

interface Props {
  message: ChatMsg;
}

function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function formatContent(text: string): string {
  // Escape HTML first to prevent XSS, then apply markdown-like formatting
  let safe = escapeHtml(text);
  return safe
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code style="background:#f3f4f6;padding:1px 4px;border-radius:3px;font-size:0.85em">$1</code>')
    .replace(/^- /gm, '• ')
    .replace(/¥([\d,]+)/g, '<span style="font-weight:600">¥$1</span>');
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
      }}
        dangerouslySetInnerHTML={isUser ? undefined : { __html: formatContent(message.content) }}
      >
        {isUser ? message.content : undefined}
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
