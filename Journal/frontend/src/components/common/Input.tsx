/* ──────────────────────────────────────────────────────────────
   Input — Styled form input with label and error display
   ────────────────────────────────────────────────────────────── */
import { forwardRef, type InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = "", id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");

    return (
      <div className="flex flex-col gap-2">
        {label && (
          <label htmlFor={inputId} className="text-sm font-semibold text-surface-700">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={`
            w-full px-5 py-3.5
            bg-white border border-surface-200
            rounded-2xl
            text-surface-800 placeholder:text-surface-400
            focus:outline-none focus:ring-4 focus:ring-primary-100 focus:border-primary-400
            transition-all duration-300
            ${error ? "border-danger-300 focus:ring-danger-100 focus:border-danger-400" : ""}
            ${className}
          `}
          {...props}
        />
        {error && <p className="text-xs text-danger-500 mt-0.5 font-medium">{error}</p>}
      </div>
    );
  }
);

Input.displayName = "Input";
export default Input;
