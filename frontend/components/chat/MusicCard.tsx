"use client";
import { useState, useEffect } from "react";
import { MusicTrack } from "@/lib/api";
import { ExternalLink } from "lucide-react";

interface MusicCardProps {
  tracks: MusicTrack[];
}

export function MusicCard({ tracks }: MusicCardProps) {
  const [visibleCount, setVisibleCount] = useState(0);

  // Reveal tracks one by one with a delay
  useEffect(() => {
    if (!tracks || tracks.length === 0) return;
    setVisibleCount(0);
    let i = 0;
    const interval = setInterval(() => {
      i += 1;
      setVisibleCount(i);
      if (i >= tracks.length) clearInterval(interval);
    }, 600); // 600ms between each track
    return () => clearInterval(interval);
  }, [tracks]);

  if (!tracks || tracks.length === 0) return null;

  return (
    <div className="mt-3 w-full bg-purple-500/10 border border-purple-500/20 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">🎵</span>
        <span className="text-xs font-semibold text-purple-300 uppercase tracking-wide">
          Music for your mood
        </span>
      </div>
      <div className="space-y-2">
        {tracks.slice(0, visibleCount).map((track, i) => (
          <div
            key={i}
            className="bg-white/5 rounded-lg p-3 flex items-start justify-between gap-3 animate-fade-in"
            style={{ animationDelay: `${i * 100}ms` }}
          >
            <div className="flex-1 min-w-0">
              <p className="text-white text-sm font-medium truncate">{track.title}</p>
              <p className="text-slate-400 text-xs">{track.artist}</p>
              <p className="text-slate-500 text-xs mt-1 leading-relaxed">{track.reason}</p>
            </div>
            <div className="flex flex-col gap-1.5 flex-shrink-0">
              <a
                href={track.spotify_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 px-2.5 py-1.5 rounded-full bg-green-500/20 border border-green-500/30 text-green-400 text-xs font-medium hover:bg-green-500/30 transition-colors"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z" />
                </svg>
                Spotify
              </a>
              <a
                href={track.youtube_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 px-2.5 py-1.5 rounded-full bg-red-500/20 border border-red-500/30 text-red-400 text-xs font-medium hover:bg-red-500/30 transition-colors"
              >
                <ExternalLink size={10} />
                YouTube
              </a>
            </div>
          </div>
        ))}
        {/* Loading dots while more tracks are coming */}
        {visibleCount < tracks.length && (
          <div className="flex gap-1 px-2 py-1">
            <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
            <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
            <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
          </div>
        )}
      </div>
    </div>
  );
}
