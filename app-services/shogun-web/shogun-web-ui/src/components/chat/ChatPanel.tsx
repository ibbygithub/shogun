"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { ChatMessage as ChatMsg } from "@/lib/types";
import ChatMessage from "./ChatMessage";

export default function ChatPanel() {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.chat.history().then((h) => setMessages(h as ChatMsg[]));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send() {
    const text = input.trim();
    if (!text || sending) return;

    const userMsg: ChatMsg = { role: "user", content: text, timestamp: Date.now() / 1000 };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);

    try {
      const res = await api.chat.send(text) as { response: string };
      const assistantMsg: ChatMsg = { role: "assistant", content: res.response, timestamp: Date.now() / 1000 };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [...prev, {
        role: "assistant",
        content: "Sorry, I couldn't reach Shogun right now. Try again in a moment.",
        timestamp: Date.now() / 1000,
      }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
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
                width: 8, height: 8, borderRadius: "50%", background: "#d1d5db",
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
  );
}
