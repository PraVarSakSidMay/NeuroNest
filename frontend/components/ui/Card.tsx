// Card.tsx — Generic white card wrapper
// Wrap any content in this to get the standard card look.
// Usage: <Card className="p-6">...</Card>

import { cn } from "@/lib/utils";

type CardProps = {
  children: React.ReactNode;
  className?: string;
};

export default function Card({ children, className }: CardProps) {
  return (
    <div className={cn("soft-card p-6", className)}>
      {children}
    </div>
  );
}
