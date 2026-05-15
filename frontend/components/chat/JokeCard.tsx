"use client";
export function JokeCard({ joke }: { joke: string }) {
  return (
    <div className="mt-3 w-full bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2"><span className="text-lg">😄</span><span className="text-xs font-semibold text-yellow-300 uppercase tracking-wide">A little something to lighten the mood</span></div>
      <p className="text-slate-200 text-sm leading-relaxed">{joke}</p>
    </div>
  );
}
