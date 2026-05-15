"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to journal page
    router.push("/journal");
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
      <div className="text-center">
        <div className="animate-pulse text-4xl mb-4">🌱</div>
        <p className="text-gray-600">Loading NeuroNest...</p>
      </div>
    </div>
  );
}
