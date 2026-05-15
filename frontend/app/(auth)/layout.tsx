export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex">

      {/* ── Left hero panel — fixed width, full height ── */}
      <div
        className="hidden lg:flex lg:w-[420px] xl:w-[460px] flex-col justify-between p-12 text-white relative overflow-hidden shrink-0"
        style={{ background: "linear-gradient(145deg, #7c3aed 0%, #4f46e5 55%, #3b82f6 100%)" }}
      >
        {/* Decorative circles */}
        <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-white/10 pointer-events-none" />
        <div className="absolute -bottom-20 -right-20 w-80 h-80 rounded-full bg-white/10 pointer-events-none" />

        {/* Logo */}
        <div className="relative flex items-center gap-3 z-10">
          <div className="w-11 h-11 rounded-xl bg-white/20 flex items-center justify-center text-2xl shadow-lg">🧠</div>
          <div>
            <span className="text-xl font-bold">NeuroNest</span>
            <p className="text-xs text-white/70 mt-0.5">Wellness Platform</p>
          </div>
        </div>

        {/* Center illustration */}
        <div className="relative z-10 flex flex-col items-center text-center gap-7">
          <div className="w-44 h-44 rounded-full bg-white/15 flex items-center justify-center text-8xl shadow-2xl border border-white/20">
            🌸
          </div>
          <div>
            <h2 className="text-3xl font-bold leading-snug mb-3">
              Your mind deserves<br />a safe space.
            </h2>
            <p className="text-white/70 text-[15px] leading-relaxed max-w-[280px] mx-auto">
              Track your mood, journal your thoughts, and connect with AI-powered
              wellness support — all in one calm, private space.
            </p>
          </div>
        </div>

        {/* Feature pills */}
        <div className="relative z-10 flex flex-wrap gap-2 justify-center">
          {["Mood Tracking", "AI Chat", "Journal", "Community", "Voice Assistant"].map(f => (
            <span key={f} className="text-sm bg-white/15 border border-white/20 px-3.5 py-1.5 rounded-full font-medium">
              {f}
            </span>
          ))}
        </div>
      </div>

      {/* ── Right form panel — stable, no vertical shifting ── */}
      <div
        className="flex-1 flex items-start justify-center overflow-y-auto"
        style={{
          background: "linear-gradient(135deg, #f5f3ff 0%, #ede9fe 40%, #dbeafe 100%)",
          padding: "60px 48px",
          minHeight: "100vh",
        }}
      >
        {children}
      </div>

    </div>
  );
}
