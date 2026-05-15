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
  transition: "all 0.2s ease", marginTop: "8px",
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

const selectStyle: React.CSSProperties = {
  ...inputStyle, cursor: "pointer", appearance: "none" as const,
};

const textareaStyle: React.CSSProperties = {
  width: "100%", padding: "14px 20px", borderRadius: "12px",
  border: "2px solid #e5e7eb", background: "#f9f8ff",
  fontSize: "15px", color: "#111827", outline: "none",
  transition: "all 0.2s ease", resize: "none" as const,
};

function Field({ label, hint, error, children }: {
  label: string; hint?: string; error?: string; children: React.ReactNode;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <label style={{ fontSize: "14px", fontWeight: 600, color: "#374151" }}>{label}</label>
        {hint && <span style={{ fontSize: "12px", color: "#9ca3af" }}>{hint}</span>}
      </div>
      {children}
      {error && (
        <p style={{ fontSize: "12px", color: "#ef4444", display: "flex", alignItems: "center", gap: "4px" }}>
          ⚠ {error}
        </p>
      )}
    </div>
  );
}

function SectionDivider({ label }: { label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "4px 0" }}>
      <div style={{ flex: 1, height: "1px", background: "#e5e7eb" }} />
      <span style={{ fontSize: "11px", color: "#9ca3af", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em" }}>
        {label}
      </span>
      <div style={{ flex: 1, height: "1px", background: "#e5e7eb" }} />
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

// Form field type — now includes age
type UF = {
  firstName: string;
  lastName: string;
  age: string;
  email: string;
  password: string;
  sleepSchedule: string;
  avgSleep: string;
  lastVisit: string;
  healthIssues: string;
};

export default function SignupPage() {
  const router      = useRouter();
  const { setUser } = useUser();

  const [showPw, setShowPw]     = useState(false);
  const [loading, setLoading]   = useState(false);
  const [errors, setErrors]     = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState<string | null>(null);

  const [uf, setUf] = useState<UF>({
    firstName: "", lastName: "", age: "", email: "", password: "",
    sleepSchedule: "", avgSleep: "", lastVisit: "", healthIssues: "",
  });

  const ch = (f: keyof UF, v: string) => {
    setUf(p => ({ ...p, [f]: v }));
    setErrors(p => ({ ...p, [f]: "" }));
  };

  function validate() {
    const e: Record<string, string> = {};
    if (!uf.firstName.trim())                  e.firstName = "First name is required";
    if (!uf.lastName.trim())                   e.lastName  = "Last name is required";
    if (!uf.age.trim())                        e.age       = "Age is required";
    else if (isNaN(Number(uf.age)) || Number(uf.age) < 1 || Number(uf.age) > 120)
                                               e.age       = "Enter a valid age";
    if (!uf.email.trim())                      e.email     = "Email is required";
    else if (!/\S+@\S+\.\S+/.test(uf.email))  e.email     = "Enter a valid email";
    if (!uf.password)                          e.password  = "Password is required";
    else if (uf.password.length < 6)           e.password  = "Minimum 6 characters";
    setErrors(e);
    return !Object.keys(e).length;
  }

  async function handleSubmit(ev: React.FormEvent) {
    ev.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setApiError(null);
    try {
      const res = await api.signup.user(uf);
      localStorage.setItem("nn_token", res.access_token);
      const name = res.user.name;
      setUser({ name, role: "user", avatar: name.charAt(0).toUpperCase() });
      router.push("/dashboard");
    } catch (err) {
      setApiError(err instanceof Error ? err.message : "Sign up failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ width: "100%", maxWidth: "500px" }}>

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
            Create your account ✨
          </h2>
          <p style={{ fontSize: "15px", color: "#6b7280", marginTop: "8px" }}>
            Join NeuroNest — your wellness journey starts here
          </p>
        </div>

        <form onSubmit={handleSubmit} noValidate style={{ display: "flex", flexDirection: "column", gap: "18px" }}>

          {/* Name row */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <Field label="First Name" error={errors.firstName}>
              <input
                style={errors.firstName ? inputErrStyle : inputStyle}
                placeholder="Varsha"
                value={uf.firstName}
                onChange={e => ch("firstName", e.target.value)}
                autoComplete="given-name"
              />
            </Field>
            <Field label="Last Name" error={errors.lastName}>
              <input
                style={errors.lastName ? inputErrStyle : inputStyle}
                placeholder="Sharma"
                value={uf.lastName}
                onChange={e => ch("lastName", e.target.value)}
                autoComplete="family-name"
              />
            </Field>
          </div>

          {/* Age */}
          <Field label="Age" error={errors.age}>
            <input
              type="number"
              min="1"
              max="120"
              style={errors.age ? inputErrStyle : inputStyle}
              placeholder="e.g. 24"
              value={uf.age}
              onChange={e => ch("age", e.target.value)}
            />
          </Field>

          {/* Email */}
          <Field label="Email Address" error={errors.email}>
            <input
              type="email"
              style={errors.email ? inputErrStyle : inputStyle}
              placeholder="you@example.com"
              value={uf.email}
              onChange={e => ch("email", e.target.value)}
              autoComplete="email"
            />
          </Field>

          {/* Password */}
          <Field label="Password" error={errors.password}>
            <div style={{ position: "relative" }}>
              <input
                type={showPw ? "text" : "password"}
                style={{ ...(errors.password ? inputErrStyle : inputStyle), paddingRight: "52px" }}
                placeholder="Minimum 6 characters"
                value={uf.password}
                onChange={e => ch("password", e.target.value)}
                autoComplete="new-password"
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

          <SectionDivider label="Health Information" />

          {/* Sleep schedule */}
          <Field label="Sleep Schedule">
            <select
              style={selectStyle}
              value={uf.sleepSchedule}
              onChange={e => ch("sleepSchedule", e.target.value)}
            >
              <option value="">Select your sleep schedule</option>
              <option value="early">Early bird (before 10 PM)</option>
              <option value="normal">Normal (10 PM – midnight)</option>
              <option value="late">Night owl (after midnight)</option>
              <option value="irregular">Irregular / varies</option>
            </select>
          </Field>

          {/* Avg sleep + last visit */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <Field label="Avg. Sleep Hours">
              <input
                type="number" min="1" max="12"
                style={inputStyle}
                placeholder="e.g. 7"
                value={uf.avgSleep}
                onChange={e => ch("avgSleep", e.target.value)}
              />
            </Field>
            <Field label="Last Visit" hint="Optional">
              <input
                type="date"
                style={inputStyle}
                value={uf.lastVisit}
                onChange={e => ch("lastVisit", e.target.value)}
              />
            </Field>
          </div>

          {/* Health issues */}
          <Field label="Existing Health Issues" hint="Optional">
            <textarea
              style={textareaStyle}
              rows={3}
              placeholder="e.g. anxiety, insomnia, migraines..."
              value={uf.healthIssues}
              onChange={e => ch("healthIssues", e.target.value)}
            />
          </Field>

          {/* API error */}
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
            {loading ? <><Spinner /> Creating account...</> : "Create Account"}
          </button>
        </form>

        <div style={{ display: "flex", alignItems: "center", gap: "12px", margin: "24px 0" }}>
          <div style={{ flex: 1, height: "1px", background: "#e5e7eb" }} />
          <span style={{ fontSize: "12px", color: "#9ca3af", fontWeight: 500 }}>or</span>
          <div style={{ flex: 1, height: "1px", background: "#e5e7eb" }} />
        </div>

        <p style={{ textAlign: "center", fontSize: "15px", color: "#6b7280" }}>
          Already have an account?{" "}
          <Link href="/login" style={{ color: "#7c3aed", fontWeight: 700, textDecoration: "none" }}>
            Sign in
          </Link>
        </p>
      </div>

      <p style={{ textAlign: "center", fontSize: "12px", color: "#9ca3af", marginTop: "16px" }}>
        🔒 Your data is private and secure
      </p>
    </div>
  );
}
