"use client";
import { useEffect, useRef } from "react";
import { useChatStore } from "@/store/chatStore";
import { MessageBubble } from "./MessageBubble";
import { Brain, Loader2, Sparkles } from "lucide-react";

const WELCOME = [
  { emoji: "😤", text: "I'm really stressed" }, { emoji: "😰", text: "Feeling anxious" },
  { emoji: "😢", text: "I'm feeling sad" }, { emoji: "😊", text: "I'm doing great!" },
  { emoji: "🤯", text: "Overwhelmed" }, { emoji: "🥺", text: "Feeling lonely" },
];

export function ChatWindow() {
  const { messages, isLoading } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-2">
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-center px-4 py-12">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 to-teal-500 flex items-center justify-center mb-6 shadow-2xl shadow-purple-500/30">
            <Brain size={36} className="text-white" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Hey, I&apos;m NeuroNest 🧠</h2>
          <p className="text-slate-400 text-sm max-w-sm mb-8 leading-relaxed">Your safe space to express how you&apos;re feeling. I&apos;m here to listen, understand, and help you feel better — one conversation at a time.</p>
          <div className="flex items-center gap-2 mb-4"><Sparkles size={14} className="text-purple-400" /><span className="text-xs text-slate-500 uppercase tracking-wide font-medium">How are you feeling right now?</span></div>
          <div className="grid grid-cols-2 gap-2 w-full max-w-xs">
            {WELCOME.map((s) => <div key={s.text} className="bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-slate-300 text-center">{s.emoji} {s.text}</div>)}
          </div>
          <p className="text-xs text-slate-600 mt-8 max-w-xs">Type a message below or use the 🎙️ mic button to share how you&apos;re feeling</p>
        </div>
      ) : (
        <>
          {messages.map((m) => <MessageBubble key={m.id} message={m} />)}
          {isLoading && (
            <div className="flex gap-3 mb-6">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-teal-500 to-cyan-500 flex items-center justify-center flex-shrink-0"><Brain size={16} className="text-white" /></div>
              <div className="bg-white/8 border border-white/10 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2">
                <Loader2 size={14} className="text-purple-400 animate-spin" />
                <span className="text-slate-400 text-sm">NeuroNest is thinking...</span>
              </div>
            </div>
          )}
        </>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
