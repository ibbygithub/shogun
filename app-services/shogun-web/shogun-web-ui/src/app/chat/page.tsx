import ChatPanel from "@/components/chat/ChatPanel";

export default function ChatPage() {
  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "1rem 1.25rem", borderBottom: "1px solid #e5e7eb", background: "white" }}>
        <h1 style={{ fontSize: "1.2rem", fontWeight: 800 }}>💬 Chat with Shogun</h1>
        <p style={{ fontSize: "0.8rem", color: "#6b7280", marginTop: "0.125rem" }}>
          Your AI travel concierge for Japan 2026
        </p>
      </div>
      <div style={{ flex: 1, overflow: "hidden" }}>
        <ChatPanel />
      </div>
    </div>
  );
}
