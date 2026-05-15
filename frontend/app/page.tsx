"use client";
import { Brain, RefreshCw, Phone, History } from "lucide-react";
import Link from "next/link";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { ChatInput } from "@/components/chat/ChatInput";
import { MoodBadge } from "@/components/chat/MoodBadge";
import { useChatStore } from "@/store/chatStore";

export default function Home() {
  const { clearChat, messages } = useChatStore();
  return (
    <div className="flex flex-col h-screen bg-[#0f0f1a] overflow-hidden">
      {/* Background blobs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-teal-600/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-pink-600/5 rounded-full blur-3xl" />
      </div>

      {/* Header */}
      <header className="relative z-10 flex items-center justify-between px-4 py-3 border-b border-white/10 bg-slate-900/60 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-purple-500 to-teal-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
            <Brain size={18} className="text-white" />
          </div>
          <div>
            <h1 className="text-white font-bold text-base leading-tight">NeuroNest</h1>
            <p className="text-slate-500 text-xs">AI Wellness Companion</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <MoodBadge />

          {/* History button */}
          <Link
            href="/history"
            className="p-2 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-white/5 transition-all duration-200"
            title="View chat history"
          >
            <History size={16} />
          </Link>

          {/* Clear chat */}
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="p-2 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-white/5 transition-all duration-200"
              title="Clear chat"
            >
              <RefreshCw size={16} />
            </button>
          )}
        </div>
      </header>

      {/* Crisis Banner */}
      <div className="relative z-10 bg-red-500/10 border-b border-red-500/20 px-4 py-2 flex items-center gap-2">
        <Phone size={12} className="text-red-400" />
        <span className="text-xs text-red-300">
          In crisis? Call <strong>iCall: 9152987821</strong> (India) or <strong>988</strong> (US) — available 24/7
        </span>
      </div>

      {/* Chat */}
      <main className="relative z-10 flex-1 flex flex-col overflow-hidden">
        <ChatWindow />
        <ChatInput />
      </main>
    </div>
  );
}
