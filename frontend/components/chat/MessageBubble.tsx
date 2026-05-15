"use client";
import { useEffect, useState } from "react";
import { DisplayMessage } from "@/store/chatStore";
import { EMOTION_EMOJI, MOOD_EMOJI, MOOD_COLOR, formatMoodLabel } from "@/lib/utils";
import { ActivityCard } from "./ActivityCard";
import { SpecialActionCard } from "./SpecialActionCard";
import { MusicCard } from "./MusicCard";
import { JokeCard } from "./JokeCard";
import { ProverbCard } from "./ProverbCard";
import { CelebrationCard } from "./CelebrationCard";
import { TTSControls } from "./TTSControls";
import { useTTS } from "@/hooks/useTTS";
import { useTypewriter } from "@/hooks/useTypewriter";
import { Brain } from "lucide-react";

interface MessageBubbleProps {
  message: DisplayMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const response = message.chatResponse;
  const { speak, stop, isSpeaking, voiceGender, setVoiceGender, autoSpeak, setAutoSpeak, currentVoiceName } = useTTS();

  const mode = response?.response_mode || "support";
  const isPositiveMode = mode === "celebrate" || mode === "reflect";

  // ── Typewriter effect for assistant messages ──────────────────────────────
  const { displayed: displayedText, isDone: textDone } = useTypewriter(
    message.content,
    45,          // 45ms per word — natural speaking pace
    !isUser      // only animate assistant messages
  );

  // ── Staggered activity reveal ─────────────────────────────────────────────
  const activities = response?.activities || [];
  const [visibleActivities, setVisibleActivities] = useState(0);

  useEffect(() => {
    if (!textDone || activities.length === 0) return;
    setVisibleActivities(0);
    let i = 0;
    const interval = setInterval(() => {
      i += 1;
      setVisibleActivities(i);
      if (i >= activities.length) clearInterval(interval);
    }, 500); // 500ms between each activity
    return () => clearInterval(interval);
  }, [textDone, activities.length]);

  // ── Staggered card reveal (proverb → breathing → joke → music → tip → activities) ──
  const [showProverb, setShowProverb]       = useState(false);
  const [showSpecial, setShowSpecial]       = useState(false);
  const [showJoke, setShowJoke]             = useState(false);
  const [showMusic, setShowMusic]           = useState(false);
  const [showTip, setShowTip]               = useState(false);
  const [showActivities, setShowActivities] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);

  useEffect(() => {
    if (isUser || !textDone) return;
    // Stagger each card section after text is done
    const t1 = setTimeout(() => setShowProverb(true),     300);
    const t2 = setTimeout(() => setShowSpecial(true),     800);
    const t3 = setTimeout(() => setShowJoke(true),       1300);
    const t4 = setTimeout(() => setShowMusic(true),      1800);
    const t5 = setTimeout(() => setShowTip(true),        2300);
    const t6 = setTimeout(() => setShowActivities(true), 2800);
    const t7 = setTimeout(() => setShowCelebration(true), 800);
    return () => { [t1,t2,t3,t4,t5,t6,t7].forEach(clearTimeout); };
  }, [textDone, isUser]);

  // ── Auto-speak when text is fully rendered ────────────────────────────────
  useEffect(() => {
    if (isUser || !message.content || !autoSpeak) return;
    if (!textDone) return; // wait for typewriter to finish before speaking
    const timer = setTimeout(() => speak(message.content), 200);
    return () => { clearTimeout(timer); window.speechSynthesis?.cancel(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [textDone, message.id, isUser]);

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"} mb-6`}>

      {/* Avatar */}
      <div className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold
        ${isUser
          ? "bg-gradient-to-br from-purple-500 to-pink-500 text-white"
          : "bg-gradient-to-br from-teal-500 to-cyan-500 text-white"
        }`}
      >
        {isUser ? "You" : <Brain size={16} />}
      </div>

      {/* Content */}
      <div className={`flex-1 max-w-[85%] ${isUser ? "items-end" : "items-start"} flex flex-col`}>

        {/* Emotion badge */}
        {!isUser && response && (
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className="text-xs text-slate-400">
              {EMOTION_EMOJI[response.detected_emotion] || "💭"}{" "}
              <span className="capitalize">{response.detected_emotion}</span>
            </span>
            <span className="text-slate-600">·</span>
            <span className={`text-xs font-medium ${MOOD_COLOR[response.mood_level] || "text-slate-400"}`}>
              {MOOD_EMOJI[response.mood_level]} {formatMoodLabel(response.mood_level)}
            </span>
            {response.llm_provider && (
              <>
                <span className="text-slate-600">·</span>
                <span className="text-xs text-slate-600">{response.llm_provider}</span>
              </>
            )}
          </div>
        )}

        {/* Message bubble — typewriter for assistant */}
        <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed
          ${isUser
            ? "bg-gradient-to-br from-purple-600 to-purple-700 text-white rounded-tr-sm"
            : "bg-white/8 border border-white/10 text-slate-100 rounded-tl-sm"
          }`}
        >
          {isUser ? message.content : (
            <>
              {displayedText}
              {/* Blinking cursor while typing */}
              {!textDone && (
                <span className="inline-block w-0.5 h-4 bg-teal-400 ml-0.5 animate-pulse align-middle" />
              )}
            </>
          )}
        </div>

        {/* TTS controls */}
        {!isUser && (
          <TTSControls
            text={message.content}
            isSpeaking={isSpeaking}
            voiceGender={voiceGender}
            autoSpeak={autoSpeak}
            currentVoiceName={currentVoiceName}
            onSpeak={speak}
            onStop={stop}
            onGenderChange={setVoiceGender}
            onAutoSpeakChange={setAutoSpeak}
          />
        )}

        {/* ── POSITIVE MODE (happy / excited / calm) ─────────────────────── */}
        {!isUser && isPositiveMode && (
          <>
            {showProverb && response?.proverb && response?.proverb_author && (
              <div className="w-full animate-fade-in">
                <ProverbCard proverb={response.proverb} author={response.proverb_author} />
              </div>
            )}
            {showCelebration && response?.celebration_message && (
              <div className="w-full animate-fade-in">
                <CelebrationCard message={response.celebration_message} emotion={response.detected_emotion} />
              </div>
            )}
            {showMusic && response?.music_tracks && response.music_tracks.length > 0 && (
              <div className="w-full">
                <MusicCard tracks={response.music_tracks} />
              </div>
            )}
            {showJoke && response?.joke && (
              <div className="w-full animate-fade-in">
                <JokeCard joke={response.joke} />
              </div>
            )}
          </>
        )}

        {/* ── SUPPORT MODE ─────────────────────────────────────────────────── */}
        {!isUser && !isPositiveMode && (
          <>
            {showProverb && response?.proverb && response?.proverb_author && (
              <div className="w-full animate-fade-in">
                <ProverbCard proverb={response.proverb} author={response.proverb_author} />
              </div>
            )}
            {showSpecial && response?.special_action === "breathing_exercise" && response?.special_content && (
              <div className="w-full mt-1 animate-fade-in">
                <SpecialActionCard actionType="breathing_exercise" content={response.special_content} />
              </div>
            )}
            {showJoke && response?.joke && (
              <div className="w-full animate-fade-in">
                <JokeCard joke={response.joke} />
              </div>
            )}
            {showMusic && response?.music_tracks && response.music_tracks.length > 0 && (
              <div className="w-full">
                <MusicCard tracks={response.music_tracks} />
              </div>
            )}
            {showTip && response?.wellness_tip && (
              <div className="mt-3 w-full bg-teal-500/10 border border-teal-500/20 rounded-xl px-4 py-3 animate-fade-in">
                <p className="text-teal-300 text-xs leading-relaxed">💡 {response.wellness_tip}</p>
              </div>
            )}
            {showActivities && activities.length > 0 && (
              <div className="mt-3 w-full">
                <p className="text-xs text-slate-400 mb-2 font-medium uppercase tracking-wide animate-fade-in">
                  🎯 Suggested Activities
                </p>
                <div className="space-y-2">
                  {activities.map((activity, i) => (
                    <ActivityCard
                      key={i}
                      activity={activity}
                      index={i}
                      visible={i < visibleActivities}
                    />
                  ))}
                  {/* Loading dots while more activities are coming */}
                  {visibleActivities < activities.length && (
                    <div className="flex gap-1 px-2 py-1">
                      <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}

        {/* Timestamp */}
        <span className="text-xs text-slate-600 mt-1 px-1">
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
    </div>
  );
}
