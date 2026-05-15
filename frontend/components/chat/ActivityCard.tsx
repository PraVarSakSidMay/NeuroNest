"use client";
import { ActivitySuggestion } from "@/lib/api";
import { CATEGORY_COLOR } from "@/lib/utils";
import { Clock } from "lucide-react";

interface ActivityCardProps {
  activity: ActivitySuggestion;
  index: number;
  visible: boolean; // controlled by parent for staggered reveal
}

export function ActivityCard({ activity, index, visible }: ActivityCardProps) {
  const cat = CATEGORY_COLOR[activity.category] || "bg-slate-500/20 text-slate-300";

  if (!visible) return null;

  return (
    <div
      className="bg-white/5 border border-white/10 rounded-xl p-4 hover:bg-white/10 transition-all duration-200 hover:border-purple-500/30 animate-fade-in"
    >
      <div className="flex items-start gap-3">
        <span className="text-2xl flex-shrink-0 mt-0.5">{activity.emoji}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <h4 className="text-white font-semibold text-sm">{activity.title}</h4>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${cat}`}>
              {activity.category}
            </span>
          </div>
          <p className="text-slate-300 text-xs leading-relaxed mb-2">{activity.description}</p>
          <div className="flex items-center gap-1 text-slate-400 text-xs">
            <Clock size={11} />
            <span>{activity.duration}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
