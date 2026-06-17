/* ──────────────────────────────────────────────────────────────
   TextArea — Auto-height textarea with character counter
   ────────────────────────────────────────────────────────────── */
import { forwardRef, type TextareaHTMLAttributes } from "react";

interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  maxLength?: number;
  currentLength?: number;
}

const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(
  ({ label, error, maxLength, currentLength = 0, className = "", id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");

    return (
      <div className="flex flex-col gap-2">
        {label && (
          <label htmlFor={inputId} className="text-sm font-semibold text-surface-700">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={inputId}
          className={`
            w-full px-5 py-3.5
            bg-white border border-surface-200
            rounded-2xl
            text-surface-800 placeholder:text-surface-400
            focus:outline-none focus:ring-4 focus:ring-primary-100 focus:border-primary-400
            transition-all duration-300 resize-y min-h-[160px]
            ${error ? "border-danger-300 focus:ring-danger-100 focus:border-danger-400" : ""}
            ${className}
          `}
          {...props}
        />
        <div className="flex justify-between items-center">
          {error && <p className="text-xs text-danger-500 font-medium">{error}</p>}
          {maxLength && (
            <p className={`text-xs ml-auto font-semibold ${currentLength > maxLength ? "text-danger-500" : "text-surface-500"}`}>
              {currentLength.toLocaleString()} / {maxLength.toLocaleString()}
            </p>
          )}
        </div>
      </div>
    );
  }
);

TextArea.displayName = "TextArea";
export default TextArea;
