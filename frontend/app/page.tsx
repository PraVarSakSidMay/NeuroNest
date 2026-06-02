"use client";

import dynamic from "next/dynamic";

const VoiceAssistantClient = dynamic(
  () => import("../src/components/VoiceAssistantClient"),
  { ssr: false }
);

export default function Home() {
  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-100 via-purple-50 to-white text-slate-900 flex items-center justify-center p-8 selection:bg-indigo-200">
      <VoiceAssistantClient />
    </div>
  );
}