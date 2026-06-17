
/* ──────────────────────────────────────────────────────────────
   Protected Route — Redirects to UI login if not authenticated
   ────────────────────────────────────────────────────────────── */
import { useEffect, useState } from "react";
import { useSearchParams, Outlet } from "react-router-dom";
import { PageLoader } from "../common/Loader";

export default function ProtectedRoute() {
  const [isChecking, setIsChecking] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [searchParams] = useSearchParams();

  useEffect(() => {
    console.log("ProtectedRoute: Checking auth...");
    // Check URL query params first
    const urlToken = searchParams.get("token");
    console.log("ProtectedRoute: Token from URL:", urlToken ? "Found!" : "NOT FOUND");
    if (urlToken) {
      // Save to localStorage
      localStorage.setItem("nn_token", urlToken);
      console.log("ProtectedRoute: Token saved to localStorage!");
      // Remove token from URL for security
      const newUrl = new URL(window.location.href);
      newUrl.searchParams.delete("token");
      window.history.replaceState({}, "", newUrl.toString());
    }

    const token = localStorage.getItem("nn_token");
    console.log("ProtectedRoute: Token from localStorage:", token ? "Found!" : "NOT FOUND");
    if (token) {
      setIsAuthenticated(true);
    } else {
      console.log("ProtectedRoute: Redirecting to UI login...");
      // Redirect to UI login
      window.location.assign("http://localhost:3000/login");
    }
    setIsChecking(false);
  }, [searchParams]);

  if (isChecking || !isAuthenticated) {
    return <PageLoader />;
  }

  return <Outlet />;
}
