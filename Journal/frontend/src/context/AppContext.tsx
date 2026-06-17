/* ──────────────────────────────────────────────────────────────
   App Context — Global shared state for toast notifications
   ────────────────────────────────────────────────────────────── */
import { createContext, useContext, type ReactNode } from "react";
import { useToast, type Toast, type ToastType } from "../hooks/useToast";

interface AppContextValue {
  toasts: Toast[];
  addToast: (message: string, type?: ToastType) => void;
  dismissToast: (id: number) => void;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const { toasts, addToast, dismissToast } = useToast();

  return (
    <AppContext.Provider value={{ toasts, addToast, dismissToast }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useAppContext must be used within AppProvider");
  return ctx;
}
