// Navbar.tsx — Top bar shown on every patient page
// Shows a greeting with the user's name and a notification bell.
// Props:
//   userName → displayed in the greeting text

import { Bell, Search } from "lucide-react";

type NavbarProps = {
  userName?: string;
};

export default function Navbar({ userName = "User" }: NavbarProps) {
  // Get current hour to decide greeting
  const hour = new Date().getHours();
  const greeting =
    hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  return (
    <div className="flex items-center justify-between mb-2">
      {/* Left: greeting */}
      <div>
        <h2 className="text-xl font-bold text-[var(--color-text)]">
          {greeting}, {userName} 👋
        </h2>
        <p className="text-sm text-[var(--color-muted)]">
          Here&apos;s your wellness overview for today
        </p>
      </div>

      {/* Right: search + notification */}
      <div className="flex items-center gap-3">
        {/* Search bar */}
        <div className="hidden sm:flex items-center gap-2 bg-white border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-gray-400">
          <Search size={15} />
          <span>Search...</span>
        </div>

        {/* Notification bell */}
        <button className="relative w-9 h-9 rounded-lg bg-white border border-[var(--color-border)] flex items-center justify-center hover:bg-violet-50 transition-base">
          <Bell size={17} className="text-[var(--color-muted)]" />
          {/* Red dot for unread */}
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
        </button>

        {/* Avatar */}
        <div className="w-9 h-9 rounded-full bg-violet-600 flex items-center justify-center text-white text-sm font-bold">
          {userName.charAt(0).toUpperCase()}
        </div>
      </div>
    </div>
  );
}
