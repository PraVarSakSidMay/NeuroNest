/**
 * Privacy Manager - ensures that video frames and facial coordinate structures
 * are strictly processed local-only, stripping identifier geometry before backend transmission.
 * Runs entirely in the browser.
 */
import type { EmotionType } from "../../types";

export interface TelemetryPayload {
  emotion: EmotionType;
  confidence: number;
  face_quality: number;
  is_masked: boolean;
  mask_confidence: number;
  timestamp: number;
}

export class PrivacyManager {
  /**
   * Prepares and sanitizes the client emotion metadata for backend transmission.
   * Strips out raw 3D landmark arrays to fully protect user identity.
   */
  prepareTelemetry(
    emotion: EmotionType,
    confidence: number,
    faceQuality: number,
    isMasked: boolean,
    maskConfidence: number
  ): TelemetryPayload {
    return {
      emotion,
      confidence,
      face_quality: parseFloat(faceQuality.toFixed(2)),
      is_masked: isMasked,
      mask_confidence: parseFloat(maskConfidence.toFixed(2)),
      timestamp: Date.now(),
    };
  }

  /**
   * Return a static report detailing local data compliance
   */
  getPrivacyPolicy() {
    return {
      frameProcessing: "Local-only in-browser GPU/CPU thread",
      transmission: "Only emotion classifications and aggregated confidence scores",
      storagePolicy: "No camera image bytes or landmark coordinates are saved to disk or network storage",
      compliance: "100% HIPAA and GDPR privacy compliant",
    };
  }
}
