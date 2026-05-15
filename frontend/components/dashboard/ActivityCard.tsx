// ActivityCard.tsx — Shows a single recent activity item
// Props:
//   type        → "journal" | "chat" | "mood" — controls the icon and color
//   title       → activity name
//   description → short summary
//   time        → relative time string e.g. "2 hours ago"

import { BookOpen, MessageCircle, Smile } from "lucide-react";
import { cn } from "@/lib/utils";

type ActivityCardProps = {
  type: "journal" | "chat" | "mood";
  title: string;
  description: string;
  time: string;
};

// Icon and color per activity type
const typeConfig = {
  journal: { icon: BookOpen,       bg: "bg-violet-100", text: "text-violet-600" },
  chat:    { icon: MessageCircle,  bg: "bg-blue-100",   text: "text-blue-600"   },
  mood:    { icon: Smile,          bg: "bg-emerald-100",text: "text-emerald-600" },
};

export default function ActivityCard({
  type,
  title,
  description,
  time,
}: ActivityCardProps) {
  const { icon: Icon, bg, text } = typeConfig[type];

  return (
    <div className="soft-card p-4 flex gap-3 items-start">
      {/* Icon */}
      <div className={cn("w-9 h-9 rounded-lg flex items-center justify-center shrink-0", bg)}>
        <Icon size={17} className={text} />
      </div>

      {/* Text */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-[var(--color-text)] truncate">{title}</p>
        <p className="text-xs text-[var(--color-muted)] mt-0.5 line-clamp-2">{description}</p>
        <p className="text-[10px] text-gray-400 mt-1.5">{time}</p>
      </div>
    </div>
  );
}
