"use client";
const ACTION_CONFIG: Record<string, { icon: string; label: string; bgClass: string; borderClass: string }> = {
  breathing_exercise: { icon: "🌬️", label: "Guided breathing exercise", bgClass: "bg-blue-500/10", borderClass: "border-blue-500/30" },
  joke: { icon: "😄", label: "A little something to lighten the mood", bgClass: "bg-yellow-500/10", borderClass: "border-yellow-500/30" },
  music: { icon: "🎵", label: "Music for your mood", bgClass: "bg-purple-500/10", borderClass: "border-purple-500/30" },
};
export function SpecialActionCard({ actionType, content }: { actionType: string; content: string }) {
  const config = ACTION_CONFIG[actionType] || ACTION_CONFIG.breathing_exercise;
  const renderContent = (text: string) => text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? <strong key={i} className="text-white font-semibold">{part.slice(2, -2)}</strong> : <span key={i}>{part}</span>
  );
  return (
    <div className={`rounded-xl border p-4 mt-3 ${config.bgClass} ${config.borderClass}`}>
      <div className="flex items-center gap-2 mb-2"><span className="text-lg">{config.icon}</span><span className="text-xs font-medium text-slate-300 uppercase tracking-wide">{config.label}</span></div>
      <p className="text-slate-200 text-sm leading-relaxed whitespace-pre-line">{renderContent(content)}</p>
    </div>
  );
}
