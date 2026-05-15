"use client";
const EMOTION_CONFIG: Record<string, { gradient: string; border: string; icon: string }> = {
  happy: { gradient: "bg-gradient-to-br from-yellow-500/15 to-orange-500/10", border: "border-yellow-500/30", icon: "🌟" },
  excited: { gradient: "bg-gradient-to-br from-pink-500/15 to-purple-500/10", border: "border-pink-500/30", icon: "🚀" },
  calm: { gradient: "bg-gradient-to-br from-teal-500/15 to-cyan-500/10", border: "border-teal-500/30", icon: "🌿" },
};
export function CelebrationCard({ message, emotion }: { message: string; emotion: string }) {
  const config = EMOTION_CONFIG[emotion] || EMOTION_CONFIG.happy;
  return (
    <div className={`mt-3 w-full rounded-xl border p-4 ${config.gradient} ${config.border}`}>
      <div className="flex items-center gap-2 mb-2"><span className="text-xl">{config.icon}</span><span className="text-xs font-semibold text-white/70 uppercase tracking-wide">{emotion === "calm" ? "A moment to appreciate" : "Celebrate & share this feeling"}</span></div>
      <p className="text-slate-100 text-sm leading-relaxed">{message}</p>
    </div>
  );
}
