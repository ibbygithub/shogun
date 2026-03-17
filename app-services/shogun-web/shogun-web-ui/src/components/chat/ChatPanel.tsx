"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { ChatMessage as ChatMsg, Conversation, ToolAction } from "@/lib/types";
import ChatMessage from "./ChatMessage";

function formatDate(ts: number): string {
  const d = new Date(ts * 1000);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const msgDay = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  if (msgDay.getTime() === today.getTime()) return "Today";
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export default function ChatPanel() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loadingConvs, setLoadingConvs] = useState(true);
  // When true, the conversation endpoint is unavailable — single-conv fallback mode
  const [convFallback, setConvFallback] = useState(false);
  const [hoveredConvId, setHoveredConvId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const isMobile = () => typeof window !== "undefined" && window.innerWidth < 640;

  // Load conversations and current history on mount
  useEffect(() => {
    async function init() {
      setLoadingConvs(true);
      try {
        const convList = await api.chat.conversations();
        setConversations(convList.conversations);
        setCurrentId(convList.current_id);
      } catch {
        // Backend not deployed yet — fall back to single-conversation mode
        setConvFallback(true);
      }

      try {
        const history = await api.chat.history();
        setMessages(history as ChatMsg[]);
      } catch {
        setMessages([]);
      }

      setLoadingConvs(false);
    }
    init();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleNewConversation() {
    if (convFallback) return;
    try {
      const conv = await api.chat.newConversation();
      setConversations((prev) => [conv, ...prev]);
      setCurrentId(conv.id);
      setMessages([]);
    } catch {
      // Silently ignore — backend not ready
    }
  }

  async function handleActivateConversation(id: string) {
    if (id === currentId) return;
    try {
      const result = await api.chat.activateConversation(id);
      setCurrentId(result.id);
      setMessages(result.messages as ChatMsg[]);
      if (isMobile()) setSidebarOpen(false);
    } catch {
      // Silently ignore
    }
  }

  async function handleDeleteConversation(id: string) {
    try {
      await api.chat.deleteConversation(id);
      setConversations((prev) => {
        const remaining = prev.filter((c) => c.id !== id);
        if (id === currentId) {
          const next = remaining[0] ?? null;
          setCurrentId(next?.id ?? null);
          if (!next) {
            setMessages([]);
          } else {
            // Load next conversation's messages
            api.chat.activateConversation(next.id).then((r) => {
              setMessages(r.messages as ChatMsg[]);
            }).catch(() => setMessages([]));
          }
        }
        return remaining;
      });
    } catch {
      // Silently ignore
    }
  }

  async function handleClearHistory() {
    try {
      await api.chat.clearHistory();
      setMessages([]);
      if (currentId) {
        setConversations((prev) =>
          prev.map((c) =>
            c.id === currentId ? { ...c, title: "New conversation", message_count: 0 } : c
          )
        );
      }
    } catch {
      // Silently ignore
    }
  }

  async function send() {
    const text = input.trim();
    if (!text || sending) return;

    const userMsg: ChatMsg = { role: "user", content: text, timestamp: Date.now() / 1000 };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);

    try {
      const res = await api.chat.send(text) as { response: string; tool_actions?: ToolAction[] };
      const assistantMsg: ChatMsg = {
        role: "assistant",
        content: res.response,
        timestamp: Date.now() / 1000,
        tool_actions: res.tool_actions ?? [],
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // Update the current conversation's metadata in the list
      if (currentId) {
        setConversations((prev) =>
          prev.map((c) =>
            c.id === currentId
              ? { ...c, last_at: Date.now() / 1000, message_count: c.message_count + 2 }
              : c
          )
        );
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I couldn't reach Shogun right now. Try again in a moment.",
          timestamp: Date.now() / 1000,
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  const currentConv = conversations.find((c) => c.id === currentId) ?? null;

  return (
    <div style={{ display: "flex", height: "100%", overflow: "hidden", position: "relative" }}>

      {/* ── Sidebar ── */}
      {!convFallback && (
        <div
          style={{
            width: 260,
            minWidth: 260,
            borderRight: "1px solid #e5e7eb",
            display: sidebarOpen ? "flex" : "none",
            flexDirection: "column",
            background: "#f9fafb",
            // On mobile, overlay full width
            ...(isMobile() && sidebarOpen
              ? { position: "absolute", top: 0, left: 0, bottom: 0, width: "100%", zIndex: 50, background: "white" }
              : {}),
          }}
        >
          {/* Sidebar header */}
          <div style={{
            padding: "0.75rem 1rem",
            borderBottom: "1px solid #e5e7eb",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}>
            <span style={{ fontWeight: 700, fontSize: "0.95rem", color: "#111827" }}>Shogun Chat</span>
            <button
              onClick={handleNewConversation}
              style={{
                fontSize: "0.75rem",
                background: "#6366f1",
                color: "white",
                border: "none",
                borderRadius: 6,
                padding: "4px 10px",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              ✏️ New
            </button>
          </div>

          {/* Conversation list */}
          <div style={{ flex: 1, overflowY: "auto" }}>
            {loadingConvs ? (
              // Loading skeleton
              <div style={{ padding: "1rem" }}>
                {[1, 2, 3].map((i) => (
                  <div key={i} style={{
                    height: 44,
                    background: "#e5e7eb",
                    borderRadius: 6,
                    marginBottom: 6,
                    animation: "pulse 1.4s ease-in-out infinite",
                  }} />
                ))}
              </div>
            ) : conversations.length === 0 ? (
              <div style={{ padding: "1rem", fontSize: "0.8rem", color: "#9ca3af", textAlign: "center" }}>
                No conversations yet.
              </div>
            ) : (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => handleActivateConversation(conv.id)}
                  onMouseEnter={() => setHoveredConvId(conv.id)}
                  onMouseLeave={() => setHoveredConvId(null)}
                  style={{
                    padding: "0.625rem 0.875rem",
                    cursor: "pointer",
                    borderRadius: 6,
                    margin: "2px 4px",
                    background: conv.id === currentId
                      ? "#ede9fe"
                      : hoveredConvId === conv.id
                      ? "#f3f4f6"
                      : "transparent",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.25rem",
                  }}
                >
                  <div style={{ flex: 1, overflow: "hidden" }}>
                    <div style={{
                      fontSize: "0.85rem",
                      fontWeight: 500,
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      color: "#111827",
                    }}>
                      {conv.title}
                    </div>
                    <div style={{
                      fontSize: "0.7rem",
                      color: "#9ca3af",
                      display: "flex",
                      justifyContent: "space-between",
                      marginTop: "0.125rem",
                    }}>
                      <span>{formatDate(conv.last_at)}</span>
                      <span>{conv.message_count} msgs</span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteConversation(conv.id);
                    }}
                    style={{
                      fontSize: "0.75rem",
                      background: "none",
                      border: "none",
                      color: "#d1d5db",
                      cursor: "pointer",
                      padding: "2px 4px",
                      visibility: hoveredConvId === conv.id ? "visible" : "hidden",
                      flexShrink: 0,
                    }}
                    title="Delete conversation"
                  >
                    🗑
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* ── Main area ── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>

        {/* Main header */}
        <div style={{
          padding: "0.625rem 1rem",
          borderBottom: "1px solid #e5e7eb",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "white",
          gap: "0.5rem",
        }}>
          {/* Mobile sidebar toggle */}
          {!convFallback && (
            <button
              onClick={() => setSidebarOpen((o) => !o)}
              style={{
                background: "none",
                border: "none",
                fontSize: "1.1rem",
                cursor: "pointer",
                color: "#6b7280",
                padding: "0 4px",
                display: "none", // shown via inline media query substitute — always visible on small screens via flexShrink
              }}
              className="sidebar-toggle"
              aria-label="Toggle sidebar"
            >
              ☰
            </button>
          )}
          <span style={{
            fontSize: "0.9rem",
            fontWeight: 600,
            color: "#374151",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            flex: 1,
          }}>
            {currentConv?.title ?? (convFallback ? "Chat with Shogun" : "No conversation selected")}
          </span>
          {!convFallback && (
            <button
              onClick={handleClearHistory}
              style={{
                fontSize: "0.75rem",
                color: "#9ca3af",
                background: "none",
                border: "1px solid #e5e7eb",
                borderRadius: 6,
                padding: "3px 8px",
                cursor: "pointer",
                flexShrink: 0,
              }}
            >
              🗑 Clear
            </button>
          )}
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: "auto", padding: "1rem" }}>
          {messages.length === 0 && (
            <div style={{ textAlign: "center", color: "#9ca3af", marginTop: "2rem", fontSize: "0.9rem" }}>
              <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>🗡️</div>
              Ask Shogun anything about the Japan trip.
            </div>
          )}
          {messages.map((m, i) => <ChatMessage key={i} message={m} />)}
          {sending && (
            <div style={{ display: "flex", gap: "4px", padding: "0.625rem" }}>
              {[0, 1, 2].map((i) => (
                <div key={i} style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: "#d1d5db",
                  animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite`,
                }} />
              ))}
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div style={{
          display: "flex",
          gap: "0.5rem",
          padding: "0.75rem 1rem",
          borderTop: "1px solid #e5e7eb",
          background: "white",
        }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
            placeholder="Ask about the trip…"
            style={{
              flex: 1,
              padding: "0.5rem 0.875rem",
              borderRadius: "8px",
              border: "1px solid #e5e7eb",
              fontSize: "0.9rem",
              outline: "none",
            }}
            disabled={sending}
          />
          <button
            onClick={send}
            disabled={!input.trim() || sending}
            style={{
              padding: "0.5rem 1rem",
              background: "var(--city-accent)",
              color: "white",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: "0.85rem",
              opacity: (!input.trim() || sending) ? 0.5 : 1,
            }}
          >
            Send
          </button>
        </div>
      </div>

      {/* Responsive sidebar toggle — injected style so sidebar-toggle shows on mobile */}
      <style>{`
        @media (max-width: 639px) {
          .sidebar-toggle { display: block !important; }
        }
      `}</style>
    </div>
  );
}
