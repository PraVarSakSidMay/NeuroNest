// InputField.tsx — Reusable labeled input
// Props:
//   label    → text shown above the input
//   error    → red error message shown below
//   All standard HTML input props (type, placeholder, value, onChange, etc.)

import { cn } from "@/lib/utils";

type InputFieldProps = {
  label: string;
  error?: string;
  className?: string;
} & React.InputHTMLAttributes<HTMLInputElement>;

export default function InputField({
  label,
  error,
  className,
  id,
  ...props
}: InputFieldProps) {
  // Use the label text as id if no id provided
  const inputId = id ?? label.toLowerCase().replace(/\s+/g, "-");

  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={inputId}
        className="text-sm font-medium text-[var(--color-text)]"
      >
        {label}
      </label>
      <input
        id={inputId}
        className={cn(
          "w-full px-4 py-2.5 rounded-lg border text-sm",
          "border-[var(--color-border)] bg-white",
          "placeholder:text-gray-400",
          "focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent",
          "transition-all duration-200",
          error && "border-red-400 focus:ring-red-400",
          className
        )}
        {...props}
      />
      {/* Error message */}
      {error && (
        <p className="text-xs text-red-500 mt-0.5">{error}</p>
      )}
    </div>
  );
}
