/**
 * Privacy Manager
 * ----------------
 * This module is responsible for generating **privacy-safe** telemetry objects
 * from emotion-analysis results produced in the browser.
 *
 * Key privacy goal:
 * - Ensure no raw, identifying geometry (e.g., 3D face landmarks or camera
 *   frame bytes) is sent to the backend.
 *
 * This file only formats *aggregated* metadata (emotion label + confidence
 * metrics + masking status) for transmission.
 */
import type { EmotionType } from "../../types";

/**
 * TelemetryPayload
 * -----------------
 * Shape of the JSON payload intended to be sent to the backend.
 *
 * Important privacy notes:
 * - Only aggregated numeric scores are included.
 * - No spatial coordinates or raw landmark arrays are included.
 */
export interface TelemetryPayload {
  /**
   * The emotion classification label produced by the client-side emotion
   * model/pipeline.
   */
  emotion: EmotionType;

  /**
   * Client-side confidence score for the selected `emotion`.
   *
   * Expected usage:
   * - Usually in the range [0, 1], but this type does not enforce range.
   */
  confidence: number;

  /**
   * Quality score describing how suitable the face input was for analysis.
   *
   * Note:
   * - The code currently rounds this value to 2 decimals before sending.
   */
  face_quality: number;

  /**
   * Whether the face appears to be masked (e.g., wearing a face covering).
   *
   * This is a boolean aggregated signal, not an image.
   */
  is_masked: boolean;

  /**
   * Confidence score for the `is_masked` classification.
   *
   * Note:
   * - The code currently rounds this value to 2 decimals before sending.
   */
  mask_confidence: number;

  /**
   * Unix timestamp in milliseconds indicating when this telemetry object was
   * created on the client.
   */
  timestamp: number;
}

/**
 * PrivacyManager
 * --------------
 * Encapsulates the logic for preparing telemetry and returning a user-facing
 * (static) privacy compliance summary.
 */
export class PrivacyManager {
  /**
   * prepareTelemetry
   * -----------------
   * Builds a TelemetryPayload from primitive values computed on-device.
   *
   * What it fetches:
   * - It does not fetch from network or local storage.
   * - It uses the method parameters that should already be computed by the
   *   browser emotion pipeline.
   *
   * What it does:
   * - Rounds numeric quality/confidence fields to 2 decimal places.
   * - Maps camelCase parameter names to snake_case payload keys.
   * - Adds a creation timestamp.
   *
   * What it protects against:
   * - It intentionally does *not* accept or return any raw landmark arrays or
   *   image/frame data.
   */
  prepareTelemetry(
    /**
     * Emotion label produced by the client emotion detection.
     */
    emotion: EmotionType,

    /**
     * Confidence for the `emotion` label.
     */
    confidence: number,

    /**
     * Face quality score used to describe input quality for analysis.
     */
    faceQuality: number,

    /**
     * Whether a mask is detected.
     */
    isMasked: boolean,

    /**
     * Confidence for the mask detection.
     */
    maskConfidence: number
  ): TelemetryPayload {
    // Return a new object adhering to the TelemetryPayload contract.
    // The returned keys are in snake_case to match backend expectations.
    return {
      // Pass through the emotion label as-is.
      emotion,

      // Pass through the main emotion confidence as-is.
      confidence,

      // Round face quality to 2 decimal places.
      // - faceQuality.toFixed(2) converts number -> string.
      // - parseFloat(...) converts that string back -> number.
      face_quality: parseFloat(faceQuality.toFixed(2)),

      // Pass through mask presence boolean.
      is_masked: isMasked,

      // Round mask confidence to 2 decimal places.
      mask_confidence: parseFloat(maskConfidence.toFixed(2)),

      // Capture the current time (milliseconds) to aid backend correlation.
      timestamp: Date.now(),
    };
  }

  /**
   * getPrivacyPolicy
   * -----------------
   * Returns a static object describing what the client does with video-related
   * inputs.
   *
   * What it fetches:
   * - Nothing. This is a hard-coded summary.
   *
   * What it does:
   * - Provides a simple, UI-friendly description of local-only processing and
   *   limited transmission.
   */
  getPrivacyPolicy() {
    return {
      /**
       * Where video processing happens.
       */
      frameProcessing: "Local-only in-browser GPU/CPU thread",

      /**
       * What is allowed to be transmitted.
       */
      transmission:
        "Only emotion classifications and aggregated confidence scores",

      /**
       * Storage policy for images/landmarks.
       */
      storagePolicy:
        "No camera image bytes or landmark coordinates are saved to disk or network storage",

      /**
       * Compliance statement intended for display.
       *
       * Note:
       * - This is a claim string; it is not verified programmatically here.
       */
      compliance: "100% HIPAA and GDPR privacy compliant",
    };
  }
}

