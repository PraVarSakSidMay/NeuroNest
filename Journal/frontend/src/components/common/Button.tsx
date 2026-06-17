/* ──────────────────────────────────────────────────────────────
   Button — Primary reusable button component
   ────────────────────────────────────────────────────────────── */
import { motion } from "framer-motion";
import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "danger" | "ghost";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: ReactNode;
  children: ReactNode;
}

const variantStyles: Record<Variant, string> = {
  primary:
    "bg-gradient-to-r from-primary-500 to-accent-500 hover:from-primary-600 hover:to-accent-600 text-white shadow-lg shadow-primary-500/25 hover:shadow-xl hover:shadow-primary-500/30",
  secondary:
    "bg-white hover:bg-surface-50 text-surface-700 border border-surface-200 shadow-sm hover:shadow-md",
  danger:
    "bg-danger-50 hover:bg-danger-100 text-danger-600 border border-danger-200",
  ghost:
    "bg-transparent hover:bg-surface-100 text-surface-600 hover:text-surface-800",
};

const sizeStyles: Record<Size, string> = {
  sm: "px-4 py-2 text-sm gap-2",
  md: "px-6 py-3 text-sm gap-2.5",
  lg: "px-8 py-3.5 text-base gap-3",
};

export default function Button({
  variant = "primary",
  size = "md",
  loading = false,
  icon,
  children,
  className = "",
  disabled,
  ...props
}: ButtonProps) {
  return (
    <motion.button
      whileTap={{ scale: 0.97 }}
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 400, damping: 17 }}
      className={`
        inline-flex items-center justify-center font-semibold
        rounded-2xl cursor-pointer
        transition-all duration-300
        disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${className}
      `}
      disabled={disabled || loading}
      {...(props as any)}
    >
      {loading ? (
        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      ) : icon ? (
        <span className="flex-shrink-0">{icon}</span>
      ) : null}
      {children}
    </motion.button>
  );
}
