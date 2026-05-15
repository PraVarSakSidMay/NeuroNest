"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Brain, LayoutDashboard, MessageCircle, BookOpen,
  Mic, LogOut, ChevronLeft, ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSidebar } from "@/context/SidebarContext";
import { useUser } from "@/context/UserContext";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/chat",      label: "AI Chat",   icon: MessageCircle   },
  { href: "/journal",   label: "Journal",   icon: BookOpen        },
  { href: "/voice",     label: "Voice",     icon: Mic             },
];

export default function Sidebar() {
  const pathname              = usePathname();
  const { collapsed, toggle } = useSidebar();
  const { user, logout }      = useUser();

  const displayName   = user.name || "User";
  const displayAvatar = displayName.charAt(0).toUpperCase();

  return (
    <aside
      className={cn(
        "fixed top-0 left-0 h-screen flex flex-col z-40",
        "bg-white border-r border-gray-100",
        "shadow-[2px_0_20px_rgba(0,0,0,0.06)]",
        "transition-all duration-300 ease-in-out",
        collapsed ? "w-[68px]" : "w-[220px]"
      )}
    >
      {/* ── Brand ── */}
      <div className={cn(
        "flex items-center border-b border-gray-100 h-16 shrink-0 px-3",
        collapsed ? "justify-center" : "gap-3"
      )}>
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-600 to-blue-500 flex items-center justify-center shadow-sm shrink-0">
          <Brain size={16} className="text-white" />
        </div>
        {!collapsed && (
          <div className="min-w-0 overflow-hidden">
            <p className="font-bold text-gray-900 text-sm leading-tight">NeuroNest</p>
            <p className="text-[10px] text-gray-400">Wellness Platform</p>
          </div>
        )}
      </div>

      {/* ── Nav links ── */}
      <nav className="flex-1 px-2 py-4 space-y-0.5 overflow-y-auto overflow-x-hidden">
        {nav.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              title={collapsed ? label : undefined}
              className={cn(
                "flex items-center rounded-xl transition-all duration-150 group relative",
                collapsed
                  ? "justify-center w-10 h-10 mx-auto"
                  : "gap-3 px-3 py-2.5 w-full",
                active
                  ? "bg-violet-50 text-violet-600"
                  : "text-gray-500 hover:bg-gray-50 hover:text-gray-800"
              )}
            >
              <Icon
                size={18}
                className={cn(
                  "shrink-0",
                  active ? "text-violet-600" : "text-gray-400 group-hover:text-gray-700"
                )}
              />
              {!collapsed && (
                <span className={cn("text-sm truncate", active ? "font-semibold" : "font-medium")}>
                  {label}
                </span>
              )}
              {collapsed && active && (
                <span className="absolute right-0.5 top-1/2 -translate-y-1/2 w-1 h-4 rounded-full bg-violet-600" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* ── Collapse toggle ── */}
      <div className={cn("px-2 pb-1", collapsed ? "flex justify-center" : "")}>
        <button
          onClick={toggle}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className={cn(
            "flex items-center gap-2 rounded-xl text-gray-400",
            "hover:text-gray-700 hover:bg-gray-50",
            "transition-all duration-150 text-xs font-medium",
            collapsed ? "w-10 h-10 justify-center" : "w-full px-3 py-2"
          )}
        >
          {collapsed
            ? <ChevronRight size={16} />
            : <><ChevronLeft size={16} /><span>Collapse</span></>
          }
        </button>
      </div>

      {/* ── User + logout ── */}
      <div className={cn(
        "border-t border-gray-100 py-3 shrink-0",
        collapsed ? "px-2" : "px-3"
      )}>
        {!collapsed && (
          <div className="flex items-center gap-2.5 px-2 py-2 mb-1">
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-600 to-blue-500 flex items-center justify-center text-white text-xs font-bold shrink-0">
              {displayAvatar}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-gray-800 truncate">{displayName}</p>
              <p className="text-[10px] text-gray-400">User</p>
            </div>
          </div>
        )}
        <button
          onClick={() => { logout(); window.location.href = "/login"; }}
          title={collapsed ? "Logout" : undefined}
          className={cn(
            "flex items-center rounded-xl text-gray-400",
            "hover:bg-red-50 hover:text-red-500",
            "transition-all duration-150 text-sm font-medium",
            collapsed ? "w-10 h-10 justify-center mx-auto" : "gap-3 w-full px-3 py-2"
          )}
        >
          <LogOut size={16} className="shrink-0" />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  );
}
