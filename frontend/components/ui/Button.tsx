// Button.tsx — Reusable button component
// Props:
//   variant → "primary" (filled purple) | "outline" (bordered) | "ghost" (no bg)
//   loading → shows a spinner and disables the button
//   className → lets you add extra Tailwind classes from outside

"use client";

import { cn } from "@/lib/utils";

type ButtonProps = {
  children: React.ReactNode;
  variant?: "primary" | "outline" | "ghost";
  loading?: boolean;
  className?: string;
} & React.ButtonHTMLAttributes<HTMLButtonElement>;

export default function Button({
  children,
  variant = "primary",
  loading = false,
  className,
  disabled,
  ...props
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg font-medium text-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-500 disabled:opacity-60 disabled:cursor-not-allowed";

  const variants = {
    primary:
      "bg-violet-600 text-white hover:bg-violet-700 active:scale-[0.98] shadow-sm",
    outline:
      "border-2 border-violet-600 text-violet-600 hover:bg-violet-50 active:scale-[0.98]",
    ghost:
      "text-violet-600 hover:bg-violet-50 active:scale-[0.98]",
  };

  return (
    <button
      className={cn(base, variants[variant], className)}
      disabled={disabled || loading}
      {...props}
    >
      {/* Spinner shown when loading */}
      {loading && (
        <svg
          className="animate-spin h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12" cy="12" r="10"
            stroke="currentColor" strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8v8H4z"
          />
        </svg>
      )}
      {children}
    </button>
  );
}
