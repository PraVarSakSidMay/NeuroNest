import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  // DEMO MODE: Skip authentication check
  // In production, this would verify the Supabase auth cookie
  return NextResponse.next();
}

export const config = {
  matcher: ["/journal", "/journal/:path*"],
};
