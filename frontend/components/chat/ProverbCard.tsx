"use client";
export function ProverbCard({ proverb, author }: { proverb: string; author: string }) {
  return (
    <div className="mt-3 w-full bg-indigo-500/10 border border-indigo-500/20 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2"><span className="text-lg">🧠</span><span className="text-xs font-semibold text-indigo-300 uppercase tracking-wide">Wisdom from mental wellness experts</span></div>
      <blockquote className="text-slate-200 text-sm leading-relaxed italic">&ldquo;{proverb}&rdquo;</blockquote>
      <p className="text-indigo-400 text-xs mt-2 font-medium">— {author}</p>
    </div>
  );
}
