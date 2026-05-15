"use client";
import { useState, KeyboardEvent } from "react";
import { Send, Loader2 } from "lucide-react";
import { VoiceRecorder } from "./VoiceRecorder";
import { sendChatMessage } from "@/lib/api";
import { useChatStore } from "@/store/chatStore";

const QUICK_PROMPTS = [
  "I'm feeling really stressed today 😤", "I can't stop feeling anxious 😰",
  "I feel so lonely lately 🥺", "I'm overwhelmed with everything 🤯", "I'm actually feeling good today! 😊",
];

export function ChatInput() {
  const [input, setInput] = useState("");
  const { isLoading, sessionId, setLoading, setSessionId, addUserMessage, addAssistantMessage, setCurrentMood, getHistory } = useChatStore();

  const handleSend = async (message?: string) => {
    const text = (message || input).trim();
    if (!text || isLoading) return;
    setInput("");

    // Capture history BEFORE adding the new message — this is the conversation so far
    const history = getHistory();

    addUserMessage(text);
    setLoading(true);
    try {
      const response = await sendChatMessage(text, history, sessionId || undefined);
      if (!sessionId) setSessionId(response.session_id);
      addAssistantMessage(response.response, response);
      setCurrentMood(response.detected_emotion, response.mood_level);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Something went wrong";
      addAssistantMessage(`I'm having a little trouble connecting right now. Please try again in a moment. (${msg})`, {
        response: "", detected_emotion: "neutral", mood_level: "neutral", response_mode: "support",
        activities: [], celebration_message: null, special_action: null, special_content: null,
        music_tracks: null, joke: null, proverb: null, proverb_author: null,
        session_id: sessionId || "", wellness_tip: null, llm_provider: null,
      });
    } finally { setLoading(false); }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <div className="border-t border-white/10 bg-slate-900/80 backdrop-blur-sm p-4">
      <div className="flex gap-2 mb-3 overflow-x-auto pb-1 scrollbar-hide">
        {QUICK_PROMPTS.map((p) => (
          <button key={p} onClick={() => handleSend(p)} disabled={isLoading}
            className="flex-shrink-0 text-xs px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-slate-300 hover:bg-purple-500/20 hover:border-purple-500/30 hover:text-purple-300 transition-all duration-200 disabled:opacity-50">
            {p}
          </button>
        ))}
      </div>
      <div className="flex items-end gap-3">
        <VoiceRecorder />
        <div className="flex-1 relative">
          <textarea value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown}
            placeholder="Share how you're feeling... (Press Enter to send)" disabled={isLoading} rows={1}
            className="w-full bg-white/5 border border-white/10 rounded-2xl px-4 py-3 text-sm text-white placeholder-slate-500 resize-none focus:outline-none focus:border-purple-500/50 focus:bg-white/8 transition-all duration-200 disabled:opacity-50 max-h-32 overflow-y-auto"
            style={{ minHeight: "48px" }} />
        </div>
        <button onClick={() => handleSend()} disabled={!input.trim() || isLoading}
          className="p-3 rounded-full bg-gradient-to-br from-purple-600 to-pink-600 text-white hover:from-purple-500 hover:to-pink-500 transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0 shadow-lg shadow-purple-500/20">
          {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
        </button>
      </div>
      <p className="text-center text-xs text-slate-600 mt-2">NeuroNest is a wellness companion, not a substitute for professional mental health care.</p>
    </div>
  );
}
