"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Eye, EyeOff, Brain } from "lucide-react";
import { useUser } from "@/context/UserContext";
import { api } from "@/lib/api";

const gradientBtn: React.CSSProperties = {
  display: "flex", alignItems: "center", justifyContent: "center", gap: "8px",
  width: "100%", height: "52px", borderRadius: "14px", border: "none",
  background: "linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%)",
  color: "#ffffff", fontSize: "15px", fontWeight: 600, cursor: "pointer",
  transition: "all 0.2s ease", marginTop: "4px",
};

const inputStyle: React.CSSProperties = {
  width: "100%", height: "52px", padding: "0 20px",
  borderRadius: "12px", border: "2px solid #e5e7eb",
  background: "#f9f8ff", fontSize: "15px", color: "#111827", outline: "none",
  transition: "all 0.2s ease",
};

const inputErrStyle: React.CSSProperties = {
  ...inputStyle, border: "2px solid #f87171", background: "#fff5f5",
};

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      <label style={{ fontSize: "14px", fontWeight: 600, color: "#374151" }}>{label}</label>
      {children}
      {error && (
        <p style={{ fontSize: "12px", color: "#ef4444", display: "flex", alignItems: "center", gap: "4px" }}>
          ⚠ {error}
        </p>
      )}
    </div>
  );
}

function Spinner() {
  return (
    <svg className="animate-spin-slow" width="20" height="20" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeOpacity="0.25" />
      <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export default function LoginPage() {
  const router      = useRouter();
  const { setUser } = useUser();

  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw]     = useState(false);
  const [loading, setLoading]   = useState(false);
  const [errors, setErrors]     = useState<{ email?: string; password?: string }>({});
  const [apiError, setApiError] = useState<string | null>(null);

  function validate() {
    const e: typeof errors = {};
    if (!email.trim())                     e.email    = "Email is required";
    else if (!/\S+@\S+\.\S+/.test(email)) e.email    = "Enter a valid email";
    if (!password)                         e.password = "Password is required";
    setErrors(e);
    return !Object.keys(e).length;
  }

  async function handleSubmit(ev: React.FormEvent) {
    ev.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setApiError(null);
    try {
      const res = await api.login(email, password);
      localStorage.setItem("nn_token", res.access_token);
      const name = res.user.name;
      setUser({ name, role: "user", avatar: name.charAt(0).toUpperCase() });
      router.push("/dashboard");
    } catch (err) {
      setApiError(err instanceof Error ? err.message : "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ width: "100%", maxWidth: "480px" }}>

      {/* Mobile logo */}
      <div className="flex flex-col items-center mb-8 lg:hidden">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-600 to-blue-500 flex items-center justify-center mb-3 shadow-lg">
          <Brain size={28} className="text-white" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900">NeuroNest</h1>
        <p className="text-sm text-gray-500 mt-1">Your emotional wellness companion</p>
      </div>

      {/* Card */}
      <div style={{
        background: "#ffffff", borderRadius: "24px",
        border: "1px solid #f0eeff",
        boxShadow: "0 12px 56px rgba(124,58,237,0.13)",
        padding: "40px",
      }}>

        <div style={{ marginBottom: "28px" }}>
          <h2 style={{ fontSize: "26px", fontWeight: 700, color: "#111827", lineHeight: 1.3 }}>
            Welcome back 👋
          </h2>
          <p style={{ fontSize: "15px", color: "#6b7280", marginTop: "8px" }}>
            Sign in to continue your wellness journey
          </p>
        </div>

        <form onSubmit={handleSubmit} noValidate style={{ display: "flex", flexDirection: "column", gap: "20px" }}>

          <Field label="Email Address" error={errors.email}>
            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={e => { setEmail(e.target.value); setErrors(p => ({ ...p, email: undefined })); }}
              style={errors.email ? inputErrStyle : inputStyle}
              autoComplete="email"
            />
          </Field>

          <Field label="Password" error={errors.password}>
            <div style={{ position: "relative" }}>
              <input
                type={showPw ? "text" : "password"}
                placeholder="Enter your password"
                value={password}
                onChange={e => { setPassword(e.target.value); setErrors(p => ({ ...p, password: undefined })); }}
                style={{ ...(errors.password ? inputErrStyle : inputStyle), paddingRight: "52px" }}
                autoComplete="current-password"
              />
              <button
                type="button"
                onClick={() => setShowPw(v => !v)}
                style={{
                  position: "absolute", right: "16px", top: "50%", transform: "translateY(-50%)",
                  background: "none", border: "none", cursor: "pointer", color: "#9ca3af", padding: 0,
                }}
              >
                {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </Field>

          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "-8px" }}>
            <button type="button" style={{ background: "none", border: "none", fontSize: "13px", color: "#7c3aed", cursor: "pointer", fontWeight: 500 }}>
              Forgot password?
            </button>
          </div>

          {apiError && (
            <p style={{
              fontSize: "14px", color: "#ef4444", background: "#fef2f2",
              border: "1px solid #fecaca", borderRadius: "10px",
              padding: "10px 14px", textAlign: "center",
            }}>
              ⚠ {apiError}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{ ...gradientBtn, opacity: loading ? 0.7 : 1, cursor: loading ? "not-allowed" : "pointer" }}
          >
            {loading ? <><Spinner /> Signing in...</> : "Sign In"}
          </button>
        </form>

        <div style={{ display: "flex", alignItems: "center", gap: "12px", margin: "24px 0" }}>
          <div style={{ flex: 1, height: "1px", background: "#e5e7eb" }} />
          <span style={{ fontSize: "12px", color: "#9ca3af", fontWeight: 500 }}>or</span>
          <div style={{ flex: 1, height: "1px", background: "#e5e7eb" }} />
        </div>

        <p style={{ textAlign: "center", fontSize: "15px", color: "#6b7280" }}>
          Don&apos;t have an account?{" "}
          <Link href="/signup" style={{ color: "#7c3aed", fontWeight: 700, textDecoration: "none" }}>
            Create one free
          </Link>
        </p>
      </div>

      <p style={{ textAlign: "center", fontSize: "12px", color: "#9ca3af", marginTop: "16px" }}>
        🔒 Your data is private and secure
      </p>
    </div>
  );
}
