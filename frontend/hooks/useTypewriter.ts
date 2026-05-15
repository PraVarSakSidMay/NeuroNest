"use client";
import { useState, useEffect, useRef } from "react";

/**
 * Typewriter hook — reveals text word by word.
 * @param text - full text to animate
 * @param speed - ms between words (default 60ms)
 * @param enabled - whether to animate (default true)
 */
export function useTypewriter(text: string, speed = 60, enabled = true) {
  const [displayed, setDisplayed] = useState(enabled ? "" : text);
  const [isDone, setIsDone] = useState(!enabled);
  const indexRef = useRef(0);
  const wordsRef = useRef<string[]>([]);

  useEffect(() => {
    if (!enabled || !text) {
      setDisplayed(text);
      setIsDone(true);
      return;
    }

    // Reset on new text
    wordsRef.current = text.split(" ");
    indexRef.current = 0;
    setDisplayed("");
    setIsDone(false);

    const interval = setInterval(() => {
      indexRef.current += 1;
      const words = wordsRef.current.slice(0, indexRef.current);
      setDisplayed(words.join(" "));

      if (indexRef.current >= wordsRef.current.length) {
        clearInterval(interval);
        setIsDone(true);
      }
    }, speed);

    return () => clearInterval(interval);
  }, [text, speed, enabled]);

  return { displayed, isDone };
}
