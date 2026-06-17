/* ──────────────────────────────────────────────────────────────
   Navbar — Top navigation bar (mobile toggle + breadcrumb)
   ────────────────────────────────────────────────────────────── */
import { useLocation } from "react-router-dom";
import Button from "../common/Button";

interface NavbarProps {
  onMenuToggle: () => void;
}

const pageTitles: Record<string, string> = {
  "/": "Dashboard",
  "/journal": "Journal",
  "/journal/new": "New Entry",
  "/reflections": "Reflections",
  "/timeline": "Timeline",
};

export default function Navbar({ onMenuToggle }: NavbarProps) {
  const location = useLocation();

  // Determine page title from path
  let pageTitle = pageTitles[location.pathname] || "";
  if (location.pathname.match(/^\/journal\/[^/]+\/edit$/)) pageTitle = "Edit Entry";
  if (location.pathname.match(/^\/journal\/[^/]+$/) && !location.pathname.includes("new")) pageTitle = "View Entry";

  return (
    <header className="sticky top-0 z-30 flex items-center h-20 px-4 lg:px-8 border-b border-surface-200/50 bg-white/80 backdrop-blur-xl">
      {/* Mobile menu button */}
      <button
        onClick={onMenuToggle}
        className="lg:hidden p-3 mr-4 rounded-2xl text-surface-600 hover:text-surface-800 hover:bg-surface-100 transition-colors cursor-pointer"
      >
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
        </svg>
      </button>

      {/* Back to UI button */}
      <Button
        variant="secondary"
        onClick={() => window.location.href = "http://localhost:3000/dashboard"}
        className="mr-4"
        icon={
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
          </svg>
        }
      >
        Back to UI
      </Button>

      {/* Page title */}
      <h1 className="text-2xl font-bold gradient-text">{pageTitle}</h1>

      {/* Right side */}
      <div className="ml-auto flex items-center gap-3">
        <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white text-base font-bold shadow-lg shadow-primary-500/25">
          U
        </div>
      </div>
    </header>
  );
}
