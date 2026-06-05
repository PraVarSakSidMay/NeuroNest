"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

const RLDashboard = dynamic(
  () => import("../../src/components/RLDashboard"),
  { ssr: false }
);

export default function RLPage() {
  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-100 via-purple-50 to-white text-slate-900 p-8">
      <div className="max-w-3xl mx-auto">
        <div className="mb-6 flex items-center gap-3">
          <Link
            href="/"
            className="flex items-center gap-1.5 text-sm text-indigo-600 hover:underline"
          >
            <ArrowLeft size={14} />
            Back to NeuroNest
          </Link>
        </div>
        <RLDashboard />
      </div>
    </div>
  );
}
