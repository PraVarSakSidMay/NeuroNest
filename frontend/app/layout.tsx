import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { UserProvider } from "@/context/UserContext";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });

export const metadata: Metadata = {
  title: "NeuroNest — Your Wellness Companion",
  description: "AI-powered mental wellness and mood tracking platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen antialiased">
        {/* UserProvider wraps everything so name/role is available app-wide */}
        <UserProvider>
          {children}
        </UserProvider>
      </body>
    </html>
  );
}
