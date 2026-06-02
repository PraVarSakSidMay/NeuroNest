/**
 * Multimodal Fusion Engine - fuses video emotion predictions, audio indicators,
 * and conversational context. Performs contradiction and mask detection.
 * Runs entirely in the browser.
 */
import type { EmotionType, AudioFeatures } from "../../types";

export interface FusedEmotionResult {
  emotion: EmotionType;
  confidence: number;
  isMasked: boolean;
  maskConfidence: number;
  recommendation: string;
}

export class MultimodalFusionEngine {
  /**
   * Fuse video emotion, real-time voice features, and previous turn's text emotion.
   */
  fuseEmotions(
    videoEmotion: { emotion: EmotionType; confidence: number },
    audioFeatures: AudioFeatures | null,
    lastContextEmotion: EmotionType = "neutral"
  ): FusedEmotionResult {
    // 1. Map client-side audio features to a heuristic audio emotion
    const audioEmotion = this.estimateAudioEmotion(audioFeatures);

    // 2. Weights: video gets primary weight, audio and context help calibrating
    let weightVideo = 0.5;
    let weightAudio = 0.3;
    let weightContext = 0.2;

    // 3. Count agreement between video, audio, and text context
    const videoAudioMatch = videoEmotion.emotion === audioEmotion.emotion;
    const videoContextMatch = videoEmotion.emotion === lastContextEmotion;
    const audioContextMatch = audioEmotion.emotion === lastContextEmotion;

    const agreementCount = [videoAudioMatch, videoContextMatch, audioContextMatch].filter(Boolean).length;

    // Adjust weights based on agreement
    if (agreementCount === 3) {
      // High agreement: boost confidence of the primary video signal
      weightVideo = 0.6;
      weightAudio = 0.25;
      weightContext = 0.15;
    } else if (agreementCount === 0) {
      // Absolute disagreement: flatten weights to avoid overconfidence in any one sensor
      weightVideo = 0.4;
      weightAudio = 0.3;
      weightContext = 0.3;
    }

    // 4. Calculate final fused emotion score via weighted voting
    const emotionScores: Record<EmotionType, number> = {
      neutral: 0,
      happy: 0,
      sad: 0,
      angry: 0,
      anxious: 0,
      fearful: 0,
      surprised: 0,
      disgusted: 0,
      confused: 0,
      excited: 0,
      frustrated: 0,
      depressed: 0,
      calm: 0,
    };

    emotionScores[videoEmotion.emotion] += videoEmotion.confidence * weightVideo;
    emotionScores[audioEmotion.emotion] += audioEmotion.confidence * weightAudio;
    emotionScores[lastContextEmotion] += 0.5 * weightContext; // baseline confidence for context

    let fusedEmotion: EmotionType = "neutral";
    let maxScore = 0;

    for (const [e, score] of Object.entries(emotionScores)) {
      if (score > maxScore) {
        maxScore = score;
        fusedEmotion = e as EmotionType;
      }
    }

    // 5. Calculate fused confidence
    const rawConfidence =
      weightVideo * videoEmotion.confidence +
      weightAudio * audioEmotion.confidence +
      weightContext * 0.5;
    const fusedConfidence = parseFloat(Math.min(0.95, Math.max(0.1, rawConfidence)).toFixed(2));

    // 6. Detect Contradiction / Frown-Smile Masking
    // Triggered when face displays positive expression (happy) but voice features or context express high distress
    const isVoiceDistressed =
      audioEmotion.emotion === "sad" ||
      audioEmotion.emotion === "anxious" ||
      audioEmotion.emotion === "angry" ||
      audioEmotion.emotion === "frustrated" ||
      audioEmotion.emotion === "depressed";
    const isContextDistressed =
      lastContextEmotion === "sad" ||
      lastContextEmotion === "anxious" ||
      lastContextEmotion === "angry" ||
      lastContextEmotion === "frustrated" ||
      lastContextEmotion === "depressed";

    const isMasked = videoEmotion.emotion === "happy" && (isVoiceDistressed || isContextDistressed);
    
    let maskConfidence = 0;
    if (isMasked) {
      // Masking confidence is the difference between happy face and estimated sadness level
      maskConfidence = parseFloat(
        Math.abs(videoEmotion.confidence - (audioEmotion.confidence + 0.5) / 2).toFixed(2)
      );
    }

    // 7. Generate a helpful wellness recommendation for troubled individuals
    const recommendation = this.generateRecommendation(
      fusedEmotion,
      fusedConfidence,
      isMasked,
      audioEmotion.emotion
    );

    return {
      emotion: fusedEmotion,
      confidence: fusedConfidence,
      isMasked,
      maskConfidence,
      recommendation,
    };
  }

  /**
   * Estimate audio emotion from raw audio features
   */
  private estimateAudioEmotion(features: AudioFeatures | null): { emotion: EmotionType; confidence: number } {
    if (!features) {
      return { emotion: "neutral", confidence: 0.3 };
    }

    if (features.is_crying) {
      return { emotion: "sad", confidence: 0.85 };
    }
    if (features.is_trembling) {
      return { emotion: "anxious", confidence: 0.75 };
    }
    if (features.is_whispering) {
      return { emotion: "anxious", confidence: 0.5 };
    }

    // If pitch standard deviation is extremely high and volume is high, indicate excitement or anger
    if (features.pitch_std_dev > 25 && features.loudness > 0.3) {
      return { emotion: "excited", confidence: 0.7 };
    }
    if (features.volume_std_dev > 20 && features.loudness > 0.4) {
      return { emotion: "angry", confidence: 0.65 };
    }

    return { emotion: "neutral", confidence: 0.5 };
  }

  /**
   * Generate compassionate micro-interventions for distressed or masked states
   */
  private generateRecommendation(
    emotion: EmotionType,
    confidence: number,
    isMasked: boolean,
    audioEmotion: EmotionType
  ): string {
    if (isMasked) {
      return "I notice a smile, but I can hear some strain in your voice. It is completely okay to share what is really on your mind.";
    }

    if (confidence < 0.45) {
      return "I'm sensing some mixed emotions. Take a deep breath and tell me how you are feeling right now.";
    }

    const responses: Record<EmotionType, string> = {
      happy: "You seem to be in a warm, positive space. I am so glad to share this moment with you!",
      sad: "I sense some heaviness or sadness. I am right here with you, and we can talk about whatever you need.",
      angry: "It sounds like there is some frustration or intensity. Feel free to vent; I am listening.",
      anxious: "I can sense some tension or anxiety. Try taking a slow, deep breath. You are in a safe space.",
      fearful: "I detect some worry or fear. Remember, you do not have to face this alone. I am here.",
      surprised: "Oh, that sounds like a bit of a surprise! What happened?",
      disgusted: "Something seems to be bothering or upsetting you. Let's talk about it.",
      confused: "It sounds like you are working through some mixed thoughts. Let's unpack them together.",
      excited: "Wow, I can feel your energy! Tell me more about what is exciting you.",
      neutral: "You are keeping things steady. Whenever you are ready, I am here to chat.",
      frustrated: "I sense some frustration building up. Take your time, vent as much as you need, and we can sort it out.",
      depressed: "I detect a very heavy or despondent energy. Please know that you are not alone, and it's okay to feel this way. I'm here to listen.",
      calm: "You seem very peaceful and relaxed. It's wonderful to be in this calm headspace with you.",
    };

    return responses[emotion] || "I am listening closely. Tell me more.";
  }
}
