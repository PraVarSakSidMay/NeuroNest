import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NeuroNest — AI Mental Wellness Companion",
  description: "Your safe space to express feelings, track mood, and receive personalized wellness support.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-[#0f0f1a]">{children}</body>
    </html>
  );
}
