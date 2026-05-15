"use client";

/**
 * SidebarContext — shares collapsed state between Sidebar and layout.
 * When sidebar collapses, the main content automatically expands.
 *
 * Usage:
 *   - Wrap layout in <SidebarProvider>
 *   - Sidebar reads/writes collapsed state via useSidebar()
 *   - Layout reads collapsed state to adjust left padding
 */

import { createContext, useContext, useState } from "react";

type SidebarCtx = {
  collapsed: boolean;
  toggle: () => void;
};

const SidebarContext = createContext<SidebarCtx>({
  collapsed: false,
  toggle: () => {},
});

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  return (
    <SidebarContext.Provider value={{ collapsed, toggle: () => setCollapsed(v => !v) }}>
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  return useContext(SidebarContext);
}
