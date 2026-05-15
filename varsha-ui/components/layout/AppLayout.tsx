"use client";

import Sidebar from "@/components/layout/Sidebar";
import { SidebarProvider, useSidebar } from "@/context/SidebarContext";

function Inner({ children }: { children: React.ReactNode }) {
  const { collapsed } = useSidebar();

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#f8f7ff" }}>
      <Sidebar />
      <main
        style={{
          flex: 1,
          minHeight: "100vh",
          overflowY: "auto",
          marginLeft: collapsed ? "68px" : "220px",
          transition: "margin-left 300ms ease",
          minWidth: 0,
        }}
      >
        <div style={{ padding: "40px 48px", maxWidth: "1400px" }}>
          {children}
        </div>
      </main>
    </div>
  );
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <Inner>{children}</Inner>
    </SidebarProvider>
  );
}
