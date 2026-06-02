/**
 * Emotion Classifier — maps MediaPipe FaceLandmarker blendshapes to emotional states.
 *
 * Uses all 52 blendshapes from @mediapipe/tasks-vision for rich facial expression analysis.
 * Each emotion is defined by a weighted combination of the most discriminative blendshapes
 * (based on FACS Action Unit → emotion mapping from Ekman's research).
 *
 * The classifier uses a softmax perceptron over blendshape activations, eye contact,
 * and head pose features.
 */
import type { EmotionType } from "../../types";

export interface EmotionPrediction {
  emotion: EmotionType;
  confidence: number;
  actionUnits: Record<string, number>;
  timestamp: number;
}

/**
 * Blendshape-based emotion feature definitions.
 * Each emotion has a set of (blendshapeName, weight) pairs representing which facial
 * movements contribute positively or negatively to that emotion.
 *
 * Weights are derived from FACS literature:
 *   Happy    = AU6 (cheek raise) + AU12 (lip corner pull) − AU4 (brow lower)
 *   Sad      = AU1 (inner brow raise) + AU15 (lip depress) − AU12
 *   Angry    = AU4 (brow lower) + AU23/24 (lip tighten/press) − AU12
 *   Fearful  = AU1 + AU2 (outer brow raise) + AU5 (upper lid) + AU20 (lip stretch)
 *   Anxious  = AU1 + AU4 + AU15 + low eye contact + head deflection
 *   Surprised= AU1 + AU2 + AU5 (wide eyes) + AU25/27 (jaw drop)
 *   Disgusted= AU9 (nose wrinkle) + AU15 − AU12
 *   Confused = AU4 + AU1 + AU23 + head tilt
 *   Excited  = AU6 + AU12 + AU25 (open mouth smile)
 *   Neutral  = all blendshapes near zero
 */
interface EmotionProfile {
  /** Blendshape weights: positive = supports this emotion, negative = contradicts */
  features: Record<string, number>;
  /** Bias term (prior probability offset) */
  bias: number;
  /** Eye contact contribution (positive = looking at camera supports this emotion) */
  eyeContactWeight: number;
  /** Head pitch deflection weight (positive = looking down supports this emotion) */
  pitchWeight: number;
}

const PROFILES: Record<EmotionType, EmotionProfile> = {
  happy: {
    features: {
      cheekSquintLeft: 2.5, cheekSquintRight: 2.5,
      mouthSmileLeft: 2.0, mouthSmileRight: 2.0,  // Reduced: smile ≠ happy
      mouthDimpleLeft: 1.0, mouthDimpleRight: 1.0,
      browDownLeft: -3.0, browDownRight: -3.0,
      mouthFrownLeft: -4.0, mouthFrownRight: -4.0,
    },
    bias: -1.0,
    eyeContactWeight: 1.5,
    pitchWeight: -0.5,
  },
  sad: {
    features: {
      browInnerUp: 5.0,
      mouthFrownLeft: 5.0, mouthFrownRight: 5.0,
      mouthShrugLower: 3.0,
      mouthSmileLeft: -6.0, mouthSmileRight: -6.0,
      browDownLeft: 1.5, browDownRight: 1.5,
      mouthLowerDownLeft: 2.0, mouthLowerDownRight: 2.0,
    },
    bias: -0.5,
    eyeContactWeight: -2.0,
    pitchWeight: 2.5,
  },
  angry: {
    features: {
      browDownLeft: 6.0, browDownRight: 6.0,
      eyeSquintLeft: 3.0, eyeSquintRight: 3.0,
      mouthPressLeft: 3.0, mouthPressRight: 3.0,
      mouthSmileLeft: -5.0, mouthSmileRight: -5.0,
      jawForward: 2.0,
      noseSneerLeft: -2.0, noseSneerRight: -2.0,
    },
    bias: -1.0,
    eyeContactWeight: 2.0,
    pitchWeight: -0.5,
  },
  fearful: {
    features: {
      browInnerUp: 4.0,
      browOuterUpLeft: 3.0, browOuterUpRight: 3.0,
      eyeWideLeft: 5.0, eyeWideRight: 5.0,
      jawOpen: 3.0,
      mouthStretchLeft: 3.0, mouthStretchRight: 3.0,
      mouthSmileLeft: -4.0, mouthSmileRight: -4.0,
    },
    bias: -2.0,
    eyeContactWeight: -1.0,
    pitchWeight: 1.0,
  },
  anxious: {
    features: {
      browInnerUp: 3.5,
      browDownLeft: 2.5, browDownRight: 2.5,
      mouthFrownLeft: 3.0, mouthFrownRight: 3.0,
      mouthPressLeft: 2.5, mouthPressRight: 2.5,
      mouthSmileLeft: -4.0, mouthSmileRight: -4.0,
      mouthPucker: 1.5,
    },
    bias: -1.5,
    eyeContactWeight: -2.5,
    pitchWeight: 2.0,
  },
  surprised: {
    features: {
      browOuterUpLeft: 6.0, browOuterUpRight: 6.0,
      eyeWideLeft: 5.0, eyeWideRight: 5.0,
      jawOpen: 4.0,
      browDownLeft: -4.0, browDownRight: -4.0,
      mouthSmileLeft: -2.0, mouthSmileRight: -2.0,
    },
    bias: -1.0,
    eyeContactWeight: 1.0,
    pitchWeight: 0.0,
  },
  disgusted: {
    features: {
      noseSneerLeft: 6.0, noseSneerRight: 6.0,
      mouthUpperUpLeft: 6.0, mouthUpperUpRight: 6.0,
      mouthFrownLeft: 3.0, mouthFrownRight: 3.0,
      browDownLeft: 2.0, browDownRight: 2.0,
      eyeSquintLeft: 2.0, eyeSquintRight: 2.0,
    },
    bias: -1.0,
    eyeContactWeight: -0.5,
    pitchWeight: 0.5,
  },
  confused: {
    features: {
      browInnerUp: 2.5,
      browDownLeft: 2.0, browDownRight: -1.0,
      browOuterUpLeft: -1.0, browOuterUpRight: 2.0,
      mouthPucker: 2.0,
      mouthLeft: 2.5, mouthRight: 2.5,
      mouthSmileLeft: -2.0, mouthSmileRight: -2.0,
    },
    bias: -2.0,
    eyeContactWeight: 0.5,
    pitchWeight: 1.0,
  },
  excited: {
    features: {
      cheekSquintLeft: 3.0, cheekSquintRight: 3.0,
      mouthSmileLeft: 5.0, mouthSmileRight: 5.0,
      jawOpen: 3.0,
      eyeWideLeft: 3.0, eyeWideRight: 3.0,
      mouthFrownLeft: -5.0, mouthFrownRight: -5.0,
    },
    bias: -2.0,
    eyeContactWeight: 2.0,
    pitchWeight: -0.5,
  },
  frustrated: {
    features: {
      browDownLeft: 5.0, browDownRight: 5.0,
      mouthFrownLeft: 3.5, mouthFrownRight: 3.5,
      mouthPressLeft: 3.0, mouthPressRight: 3.0,
      mouthSmileLeft: -4.0, mouthSmileRight: -4.0,
      eyeSquintLeft: 2.0, eyeSquintRight: 2.0,
    },
    bias: -1.5,
    eyeContactWeight: 1.0,
    pitchWeight: 1.0,
  },
  depressed: {
    features: {
      browInnerUp: 4.5,
      mouthFrownLeft: 4.5, mouthFrownRight: 4.5,
      eyeBlinkLeft: 4.0, eyeBlinkRight: 4.0,
      mouthSmileLeft: -5.5, mouthSmileRight: -5.5,
      mouthLowerDownLeft: 2.0, mouthLowerDownRight: 2.0,
    },
    bias: -1.0,
    eyeContactWeight: -3.0,
    pitchWeight: 3.5,
  },
  calm: {
    features: {
      mouthSmileLeft: -2.0, mouthSmileRight: -2.0,
      mouthFrownLeft: -2.0, mouthFrownRight: -2.0,
      browInnerUp: -2.0,
      browDownLeft: -2.0, browDownRight: -2.0,
      eyeWideLeft: -2.0, eyeWideRight: -2.0,
      noseSneerLeft: -2.0, noseSneerRight: -2.0,
      jawOpen: -2.0,
    },
    bias: 1.2,
    eyeContactWeight: 2.0,
    pitchWeight: -1.0,
  },
  neutral: {
    features: {
      mouthSmileLeft: -2.0, mouthSmileRight: -2.0,
      mouthFrownLeft: -2.0, mouthFrownRight: -2.0,
      browInnerUp: -2.0,
      browDownLeft: -2.0, browDownRight: -2.0,
      eyeWideLeft: -2.0, eyeWideRight: -2.0,
      jawOpen: -2.0,
      noseSneerLeft: -2.0, noseSneerRight: -2.0,
    },
    bias: 1.0,
    eyeContactWeight: 0.5,
    pitchWeight: -0.5,
  },
};

export class EmotionClassifier {
  /**
   * Classify emotion using MediaPipe blendshapes with a softmax perceptron.
   *
   * @param actionUnits - backward-compatible AU map (used if blendshapes unavailable)
   * @param eyeContact  - is the user making direct eye contact?
   * @param headPose    - head orientation (pitch/yaw/roll)
   * @param blendshapes - raw 52-category MediaPipe blendshape scores (optional but preferred)
   */
  classifyEmotion(
    actionUnits: Record<string, number>,
    eyeContact: boolean = true,
    headPose?: { pitch: number; yaw: number; roll: number },
    blendshapes?: Record<string, number>,
    faceApiExpressions?: Record<string, number>
  ): EmotionPrediction {
    const bs = blendshapes || {};
    const hasBlendshapes = Object.keys(bs).length > 10;

    const eyeVal = eyeContact ? 1.0 : 0.0;
    const pitchDeflection = headPose ? Math.min(1.0, Math.abs(headPose.pitch) / 30.0) : 0;

    const emotions = Object.keys(PROFILES) as EmotionType[];
    const logits: Record<string, number> = {};

    for (const emotion of emotions) {
      const profile = PROFILES[emotion];
      let logit = profile.bias;

      if (hasBlendshapes) {
        // Use rich blendshape features (52-dimensional)
        for (const [shapeName, weight] of Object.entries(profile.features)) {
          logit += weight * (bs[shapeName] || 0);
        }
      } else {
        // Fallback: use the 6-AU weights
        logit +=
          (actionUnits.AU1 || 0) * (profile.features["browInnerUp"] || 0) +
          (actionUnits.AU4 || 0) * ((profile.features["browDownLeft"] || 0) + (profile.features["browDownRight"] || 0)) / 2 +
          (actionUnits.AU6 || 0) * ((profile.features["cheekSquintLeft"] || 0) + (profile.features["cheekSquintRight"] || 0)) / 2 +
          (actionUnits.AU12 || 0) * ((profile.features["mouthSmileLeft"] || 0) + (profile.features["mouthSmileRight"] || 0)) / 2 +
          (actionUnits.AU15 || 0) * ((profile.features["mouthFrownLeft"] || 0) + (profile.features["mouthFrownRight"] || 0)) / 2 +
          (actionUnits.AU25 || 0) * (profile.features["jawOpen"] || 0);
      }

      logit += profile.eyeContactWeight * eyeVal;
      logit += profile.pitchWeight * pitchDeflection;

      logits[emotion] = logit;
    }

    if (faceApiExpressions) {
      // Direct deep learning probability influence (extremely strong and stable!)
      logits["happy"] += (faceApiExpressions.happy || 0) * 8.0;
      logits["sad"] += (faceApiExpressions.sad || 0) * 8.0;
      logits["angry"] += (faceApiExpressions.angry || 0) * 8.0;
      logits["fearful"] += (faceApiExpressions.fearful || 0) * 8.0;
      logits["disgusted"] += (faceApiExpressions.disgusted || 0) * 8.0;
      logits["surprised"] += (faceApiExpressions.surprised || 0) * 8.0;
      logits["neutral"] += (faceApiExpressions.neutral || 0) * 6.0;

      // Derived emotions:
      // Anxious: fearful/sad combo + low eye contact
      logits["anxious"] += ((faceApiExpressions.fearful || 0) * 4.0 + (faceApiExpressions.sad || 0) * 2.0);
      // Depressed: sad + neutral combo + low eye contact + low pitch
      logits["depressed"] += ((faceApiExpressions.sad || 0) * 5.0 + (faceApiExpressions.neutral || 0) * 2.0);
      // Excited: happy + surprised combo + mouth open
      logits["excited"] += ((faceApiExpressions.happy || 0) * 5.0 + (faceApiExpressions.surprised || 0) * 2.0);
      // Frustrated: angry + sad combo
      logits["frustrated"] += ((faceApiExpressions.angry || 0) * 4.0 + (faceApiExpressions.sad || 0) * 2.0);
      // Calm: high neutral + low stress
      logits["calm"] += (faceApiExpressions.neutral || 0) * 5.0;
    }

    // Apply logical override rules to resolve edge cases
    if (hasBlendshapes) {
      const getVal = (k: string) => bs[k] || 0;

      const smileVal = (getVal("mouthSmileLeft") + getVal("mouthSmileRight")) / 2;
      const eyeWide = (getVal("eyeWideLeft") + getVal("eyeWideRight")) / 2;
      const jawOpen = getVal("jawOpen");

      const eyeNarrowing = Math.max(
        getVal("cheekSquintLeft"),
        getVal("cheekSquintRight"),
        getVal("eyeSquintLeft"),
        getVal("eyeSquintRight")
      );

      const browInnerUp = getVal("browInnerUp");
      const browDown = (getVal("browDownLeft") + getVal("browDownRight")) / 2;
      const noseSneer = (getVal("noseSneerLeft") + getVal("noseSneerRight")) / 2;
      const mouthUpperUp = (getVal("mouthUpperUpLeft") + getVal("mouthUpperUpRight")) / 2;
      const mouthPress = (getVal("mouthPressLeft") + getVal("mouthPressRight")) / 2;
      const mouthRoll = (getVal("mouthRollUpper") + getVal("mouthRollLower")) / 2;

      // 1. Disgust-Smile Override
      const disgustFactor = Math.max(noseSneer, mouthUpperUp);
      if (disgustFactor > 0.12) {
        logits["disgusted"] += disgustFactor * 12.0;
        logits["happy"] -= disgustFactor * 15.0;
        logits["excited"] -= disgustFactor * 15.0;
      }

      // 2. Upper-Face Validation for Happy (Prevents lip-sync/talking false positives)
      if (smileVal > 0.12) {
        if (eyeNarrowing > 0.15 || smileVal > 0.5) {
          logits["happy"] += smileVal * 4.0;
        } else {
          logits["happy"] -= 4.0;
          logits["excited"] -= 4.0;
        }
      }

      // 3. Excited vs Happy vs Surprised separation:
      if (smileVal > 0.25) {
        if (eyeWide > 0.15 || jawOpen > 0.25) {
          logits["excited"] += 4.0;
          logits["surprised"] -= 5.0;
          logits["happy"] -= 2.0;
        } else {
          logits["happy"] += 3.0;
          logits["excited"] -= 2.0;
          logits["surprised"] -= 5.0;
        }
      }

      // 4. Upper-Face Validation for Sad/Depressed (Prevents speech mouth frown false positives)
      const mouthFrown = (getVal("mouthFrownLeft") + getVal("mouthFrownRight")) / 2;
      const mouthShrug = getVal("mouthShrugLower");

      if (mouthFrown > 0.2 || mouthShrug > 0.2) {
        if (browInnerUp > 0.12 || getVal("eyeBlinkLeft") > 0.3 || getVal("eyeBlinkRight") > 0.3) {
          logits["sad"] += 2.0;
          logits["depressed"] += 2.0;
        } else {
          logits["sad"] -= 5.0;
          logits["depressed"] -= 5.0;
        }
      }

      // 5. Upper-Face Validation for Angry/Frustrated (Prevents speech lip press false positives)
      if (browDown < 0.12 && mouthPress < 0.15 && mouthRoll < 0.15) {
        logits["angry"] -= 5.0;
        logits["frustrated"] -= 5.0;
      }

      // 6. Sad vs Anxious vs Fearful:
      if (eyeWide > 0.25 && jawOpen > 0.15) {
        logits["fearful"] += 4.0;
        logits["sad"] -= 4.0;
        logits["anxious"] -= 4.0;
        logits["depressed"] -= 4.0;
      }

      // 7. Asymmetry (Confusion):
      const browAsymmetry = Math.abs(getVal("browDownLeft") - getVal("browDownRight")) +
                            Math.abs(getVal("browOuterUpLeft") - getVal("browOuterUpRight"));
      const mouthAsymmetry = Math.abs(getVal("mouthSmileLeft") - getVal("mouthSmileRight")) +
                             Math.abs(getVal("mouthPressLeft") - getVal("mouthPressRight"));
      const skewVal = Math.max(getVal("mouthLeft"), getVal("mouthRight"));
      if (browAsymmetry > 0.25 || mouthAsymmetry > 0.25 || skewVal > 0.25) {
        logits["confused"] += (browAsymmetry + mouthAsymmetry + skewVal) * 4.0;
      }

      // 8. Calm Active Verification:
      const maxExpressive = Math.max(
        smileVal,
        mouthFrown,
        browDown,
        browInnerUp,
        disgustFactor,
        eyeWide,
        eyeNarrowing,
        getVal("mouthPucker")
      );
      if (maxExpressive < 0.12) {
        logits["calm"] += (0.12 - maxExpressive) * 15.0;
      } else {
        logits["calm"] -= 5.0;
      }
    }

    // Softmax: p_c = exp(z_c) / Σ exp(z_j)
    const maxLogit = Math.max(...Object.values(logits));
    let sumExp = 0;
    const exps: Record<string, number> = {};

    for (const emotion of emotions) {
      const e = Math.exp(logits[emotion] - maxLogit);
      exps[emotion] = e;
      sumExp += e;
    }

    let bestEmotion: EmotionType = "neutral";
    let maxProb = 0;

    for (const emotion of emotions) {
      const prob = exps[emotion] / (sumExp || 1);
      if (prob > maxProb) {
        maxProb = prob;
        bestEmotion = emotion;
      }
    }

    const confidence = Math.min(0.95, Math.max(0.1, maxProb));

    return {
      emotion: bestEmotion,
      confidence: parseFloat(confidence.toFixed(2)),
      actionUnits,
      timestamp: Date.now(),
    };
  }

  /**
   * Track expression history throughout recording session.
   * Store all detected emotions to pass as context for better AI responses.
   */
  private expressionHistory: EmotionType[] = [];

  recordExpression(emotion: EmotionType): void {
    this.expressionHistory.push(emotion);
  }

  getExpressionHistory(): EmotionType[] {
    return [...this.expressionHistory];
  }

  clearExpressionHistory(): void {
    this.expressionHistory = [];
  }
}
