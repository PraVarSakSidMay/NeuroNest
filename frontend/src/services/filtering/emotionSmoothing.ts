/**
 * Emotion Smoother - applies EMA and temporal sliding window filters
 * to prevent abrupt emotion jumping.
 */
import type { EmotionType } from "../../types";

export interface SmoothedResult {
  smoothedEmotion: EmotionType;
  smoothedConfidence: number;
}

export class EmotionSmoother {
  private history: Array<{ emotion: EmotionType; confidence: number; timestamp: number }> = [];
  private maxHistoryLength = 8;
  private emaAlpha = 0.35; // Smoothing factor (higher = more reactive, lower = more stable)

  /**
   * Smooth raw emotion and confidence predictions over a sliding window
   */
  smoothEmotion(emotion: EmotionType, confidence: number): SmoothedResult {
    this.history.push({
      emotion,
      confidence,
      timestamp: Date.now(),
    });

    if (this.history.length > this.maxHistoryLength) {
      this.history.shift();
    }

    if (this.history.length === 1) {
      return { smoothedEmotion: emotion, smoothedConfidence: confidence };
    }

    // Compute Exponential Moving Average (EMA) for confidence
    let smoothedConfidence = this.history[0].confidence;
    for (let i = 1; i < this.history.length; i++) {
      smoothedConfidence =
        this.emaAlpha * this.history[i].confidence +
        (1 - this.emaAlpha) * smoothedConfidence;
    }

    // Determine the smoothed emotion (weighted voting based on historical confidence)
    const emotionScores: Record<string, number> = {};
    this.history.forEach((h, index) => {
      // Weight recent entries higher
      const recencyWeight = (index + 1) / this.history.length;
      emotionScores[h.emotion] = (emotionScores[h.emotion] || 0) + h.confidence * recencyWeight;
    });

    let smoothedEmotion: EmotionType = "neutral";
    let maxScore = 0;

    for (const [e, score] of Object.entries(emotionScores)) {
      if (score > maxScore) {
        maxScore = score;
        smoothedEmotion = e as EmotionType;
      }
    }

    return {
      smoothedEmotion,
      smoothedConfidence: parseFloat(smoothedConfidence.toFixed(2)),
    };
  }

  /**
   * Determine if the emotional state is stable, shifting, or jumping erratically
   */
  getEmotionTrend(): "stable" | "shifting" | "unstable" {
    if (this.history.length < 3) return "unstable";

    const recent = this.history.slice(-3);
    const allMatch = recent.every((h) => h.emotion === recent[0].emotion);
    const confidenceRange =
      Math.max(...recent.map((h) => h.confidence)) -
      Math.min(...recent.map((h) => h.confidence));

    if (allMatch && confidenceRange < 0.15) {
      return "stable";
    } else if (confidenceRange < 0.3) {
      return "shifting";
    }
    return "unstable";
  }

  reset(): void {
    this.history = [];
  }
}
