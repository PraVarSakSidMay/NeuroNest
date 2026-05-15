"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();

  useEffect(() => {
    // Demo mode - automatically redirect to journal
    router.push("/journal");
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
      <div className="text-center">
        <div className="animate-pulse text-5xl mb-4">🌱</div>
        <p className="text-gray-600">Loading demo...</p>
      </div>
    </div>
  );
}
