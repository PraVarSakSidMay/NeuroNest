"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Mic, Brain, Plus, MessageSquare, Loader2 } from "lucide-react";
import { api, type ChatMessage, type ChatSession } from "@/lib/api";

export default function ChatPage() {
  const [sessions, setSessions]         = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [messages, setMessages]         = useState<ChatMessage[]>([]);
  const [input, setInput]               = useState("");
  const [typing, setTyping]             = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const bottomRef                       = useRef<HTMLDivElement>(null);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  // Load sessions on mount
  useEffect(() => {
    api.chat.getSessions()
      .then(data => {
        setSessions(data);
        // Auto-open the most recent session if one exists
        if (data.length > 0) {
          openSession(data[0].id);
        }
      })
      .catch(e => console.error("Failed to load sessions:", e))
      .finally(() => setLoadingSessions(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const openSession = useCallback(async (sessionId: string) => {
    setActiveSession(sessionId);
    setLoadingMessages(true);
    try {
      const msgs = await api.chat.getMessages(sessionId);
      setMessages(msgs);
    } catch (e) {
      console.error("Failed to load messages:", e);
    } finally {
      setLoadingMessages(false);
    }
  }, []);

  async function startNewSession() {
    try {
      const sessionId = await api.chat.createSession("New conversation");
      const newSession: ChatSession = {
        id:        sessionId,
        title:     "New conversation",
        createdAt: new Date().toISOString(),
      };
      setSessions(p => [newSession, ...p]);
      setActiveSession(sessionId);
      setMessages([]);
    } catch (e) {
      console.error("Failed to create session:", e);
    }
  }

  async function send() {
    if (!input.trim()) return;

    // If no session exists yet, create one first
    let sessionId = activeSession;
    if (!sessionId) {
      try {
        sessionId = await api.chat.createSession("New conversation");
        const newSession: ChatSession = {
          id:        sessionId,
          title:     "New conversation",
          createdAt: new Date().toISOString(),
        };
        setSessions(p => [newSession, ...p]);
        setActiveSession(sessionId);
      } catch (e) {
        console.error("Failed to create session:", e);
        return;
      }
    }

    const userText = input.trim();
    const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    // Optimistic: show user message immediately
    const tempUserMsg: ChatMessage = {
      id:   `temp-${Date.now()}`,
      role: "user",
      text: userText,
      time: now,
    };
    setMessages(p => [...p, tempUserMsg]);
    setInput("");
    setTyping(true);

    try {
      // Update session title to first message if it's still default
      const currentSession = sessions.find(s => s.id === sessionId);
      if (currentSession?.title === "New conversation") {
        const newTitle = userText.length > 40 ? userText.slice(0, 40) + "…" : userText;
        await api.chat.updateSessionTitle(sessionId!, newTitle);
        setSessions(p => p.map(s =>
          s.id === sessionId ? { ...s, title: newTitle } : s
        ));
      }

      // Send message — saves user msg + AI reply to Supabase, returns AI reply
      const aiMsg = await api.chat.send(sessionId!, userText);

      // Replace temp message with real saved message, then add AI reply
      const savedMsgs = await api.chat.getMessages(sessionId!);
      setMessages(savedMsgs);
      // Ensure AI message is included (getMessages returns all)
      void aiMsg; // already included in savedMsgs
    } catch (e) {
      console.error("Failed to send message:", e);
      // Remove the optimistic message on error
      setMessages(p => p.filter(m => m.id !== tempUserMsg.id));
    } finally {
      setTyping(false);
    }
  }

  return (
    <div style={{
      display: "flex", gap: "24px",
      height: "calc(100vh - 120px)", minHeight: "500px",
    }}>

      {/* ── Sessions sidebar ── */}
      <div style={{
        width: "240px", flexShrink: 0,
        background: "#ffffff", borderRadius: "20px",
        border: "1px solid #f0eeff",
        boxShadow: "0 2px 16px rgba(124,58,237,0.07)",
        padding: "24px", display: "flex", flexDirection: "column", gap: "20px",
      }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <h3 style={{ fontSize: "15px", fontWeight: 600, color: "#111827" }}>Chat History</h3>
          <button
            onClick={startNewSession}
            title="New conversation"
            style={{
              width: "32px", height: "32px", borderRadius: "10px",
              background: "#ede9fe", border: "none", cursor: "pointer",
              display: "flex", alignItems: "center", justifyContent: "center", color: "#7c3aed",
            }}
          >
            <Plus size={15} />
          </button>
        </div>

        {loadingSessions ? (
          <div style={{ display: "flex", justifyContent: "center", padding: "20px 0" }}>
            <Loader2 size={20} className="animate-spin" style={{ color: "#9ca3af" }} />
          </div>
        ) : sessions.length === 0 ? (
          <p style={{ fontSize: "13px", color: "#9ca3af", textAlign: "center", padding: "12px 0" }}>
            No conversations yet.<br />Start one below!
          </p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "6px", overflowY: "auto" }}>
            {sessions.map(s => (
              <button
                key={s.id}
                onClick={() => openSession(s.id)}
                style={{
                  display: "flex", alignItems: "center", gap: "10px",
                  padding: "10px 14px", borderRadius: "12px", border: "none",
                  background: activeSession === s.id ? "#ede9fe" : "transparent",
                  color: activeSession === s.id ? "#7c3aed" : "#6b7280",
                  fontSize: "14px", fontWeight: activeSession === s.id ? 600 : 500,
                  cursor: "pointer", textAlign: "left", width: "100%",
                  transition: "background 0.15s ease",
                }}
              >
                <MessageSquare size={14} style={{ flexShrink: 0 }} />
                <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {s.title}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* ── Main chat area ── */}
      <div style={{
        flex: 1, minWidth: 0,
        display: "flex", flexDirection: "column",
        background: "#ffffff", borderRadius: "20px",
        border: "1px solid #f0eeff",
        boxShadow: "0 2px 16px rgba(124,58,237,0.07)",
        overflow: "hidden",
      }}>

        {/* Header */}
        <div style={{
          display: "flex", alignItems: "center", gap: "16px",
          padding: "20px 28px", borderBottom: "1px solid #f3f4f6", flexShrink: 0,
        }}>
          <div style={{
            width: "44px", height: "44px", borderRadius: "14px",
            background: "linear-gradient(135deg, #7c3aed, #3b82f6)",
            display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
          }}>
            <Brain size={20} color="#fff" />
          </div>
          <div>
            <p style={{ fontSize: "16px", fontWeight: 600, color: "#111827" }}>NeuroBot</p>
            <p style={{ fontSize: "13px", color: "#10b981", display: "flex", alignItems: "center", gap: "6px", marginTop: "2px" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#10b981", display: "inline-block" }} />
              Always here for you
            </p>
          </div>
        </div>

        {/* Messages area */}
        <div style={{
          flex: 1, overflowY: "auto", padding: "28px",
          display: "flex", flexDirection: "column", gap: "20px",
        }}>

          {/* Loading messages */}
          {loadingMessages && (
            <div style={{ display: "flex", justifyContent: "center", padding: "40px 0" }}>
              <Loader2 size={24} className="animate-spin" style={{ color: "#9ca3af" }} />
            </div>
          )}

          {/* Empty state — no session selected */}
          {!loadingMessages && !activeSession && (
            <div style={{ textAlign: "center", padding: "60px 0", color: "#9ca3af" }}>
              <p style={{ fontSize: "32px", marginBottom: "12px" }}>🧠</p>
              <p style={{ fontSize: "16px", fontWeight: 600, color: "#374151" }}>Start a conversation</p>
              <p style={{ fontSize: "14px", marginTop: "6px" }}>
                Type a message below or click + to start a new session
              </p>
            </div>
          )}

          {/* Empty session — no messages yet */}
          {!loadingMessages && activeSession && messages.length === 0 && (
            <div style={{ textAlign: "center", padding: "60px 0", color: "#9ca3af" }}>
              <p style={{ fontSize: "32px", marginBottom: "12px" }}>💜</p>
              <p style={{ fontSize: "16px", fontWeight: 600, color: "#374151" }}>Hi, I&apos;m NeuroBot</p>
              <p style={{ fontSize: "14px", marginTop: "6px" }}>How are you feeling today?</p>
            </div>
          )}

          {/* Messages */}
          {!loadingMessages && messages.map(msg => (
            <div key={msg.id} style={{
              display: "flex",
              flexDirection: msg.role === "user" ? "row-reverse" : "row",
              alignItems: "flex-end", gap: "12px",
            }}>
              {msg.role === "ai" && (
                <div style={{
                  width: "36px", height: "36px", borderRadius: "50%",
                  background: "linear-gradient(135deg, #7c3aed, #3b82f6)",
                  display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
                }}>
                  <Brain size={15} color="#fff" />
                </div>
              )}
              <div style={{
                maxWidth: "65%", padding: "14px 18px",
                borderRadius: msg.role === "ai" ? "20px 20px 20px 6px" : "20px 20px 6px 20px",
                background: msg.role === "ai" ? "#f3f4f6" : "linear-gradient(135deg, #7c3aed, #3b82f6)",
                color: msg.role === "ai" ? "#1f2937" : "#ffffff",
                fontSize: "15px", lineHeight: 1.6,
                wordBreak: "break-word", overflowWrap: "break-word",
              }}>
                <p>{msg.text}</p>
                <p style={{
                  fontSize: "11px", marginTop: "6px",
                  color: msg.role === "ai" ? "#9ca3af" : "rgba(255,255,255,0.65)",
                }}>
                  {msg.time}
                </p>
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {typing && (
            <div style={{ display: "flex", alignItems: "flex-end", gap: "12px" }}>
              <div style={{
                width: "36px", height: "36px", borderRadius: "50%",
                background: "linear-gradient(135deg, #7c3aed, #3b82f6)",
                display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
              }}>
                <Brain size={15} color="#fff" />
              </div>
              <div style={{
                padding: "14px 18px", borderRadius: "20px 20px 20px 6px",
                background: "#f3f4f6", display: "flex", gap: "6px", alignItems: "center",
              }}>
                {[0, 0.2, 0.4].map((d, i) => (
                  <span key={i} style={{
                    width: "8px", height: "8px", borderRadius: "50%",
                    background: "#9ca3af", display: "inline-block",
                    animation: `typing 1.2s ease ${d}s infinite`,
                  }} />
                ))}
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <div style={{ padding: "20px 28px", borderTop: "1px solid #f3f4f6", flexShrink: 0 }}>
          <div style={{
            display: "flex", alignItems: "center", gap: "12px",
            background: "#f9f8ff", borderRadius: "16px",
            border: "2px solid #e5e7eb", padding: "10px 16px",
          }}>
            <input
              style={{
                flex: 1, background: "transparent", border: "none",
                fontSize: "15px", color: "#111827", outline: "none", minWidth: 0,
              }}
              placeholder="Share how you're feeling..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && !e.shiftKey && send()}
            />
            <button style={{
              width: "40px", height: "40px", borderRadius: "12px",
              background: "#f3f4f6", border: "none", cursor: "pointer",
              display: "flex", alignItems: "center", justifyContent: "center",
              color: "#6b7280", flexShrink: 0,
            }}>
              <Mic size={17} />
            </button>
            <button
              onClick={send}
              disabled={!input.trim() || typing}
              style={{
                width: "40px", height: "40px", borderRadius: "12px",
                background: "linear-gradient(135deg, #7c3aed, #3b82f6)",
                border: "none", cursor: input.trim() && !typing ? "pointer" : "not-allowed",
                display: "flex", alignItems: "center", justifyContent: "center",
                flexShrink: 0, opacity: input.trim() && !typing ? 1 : 0.5,
              }}
            >
              <Send size={16} color="#fff" />
            </button>
          </div>
          <p style={{ textAlign: "center", fontSize: "12px", color: "#9ca3af", marginTop: "10px" }}>
            NeuroBot uses AI — not a substitute for professional help
          </p>
        </div>
      </div>
    </div>
  );
}
