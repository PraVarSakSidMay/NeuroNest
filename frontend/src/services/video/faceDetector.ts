/**
 * Face Detector using @mediapipe/tasks-vision FaceLandmarker (modern API).
 *
 * Uses VIDEO runningMode for temporal tracking across sequential frames.
 * Feeds the HTMLVideoElement directly to avoid ImageData→canvas round-trips.
 * WASM + model served from /wasm/ and /models/ (fully local, offline-capable).
 */
import {
  FaceLandmarker,
  FilesetResolver,
  type FaceLandmarkerResult,
} from "@mediapipe/tasks-vision";

export interface FaceDetectionResult {
  confidence: number;
  landmarks: number[][];
  actionUnits: Record<string, number>;
  headPose: { pitch: number; yaw: number; roll: number };
  eyeContact: boolean;
  /** Raw 52-category blendshapes from MediaPipe for advanced emotion classification */
  blendshapes: Record<string, number>;
}

export class FaceDetector {
  private faceLandmarker: FaceLandmarker | null = null;
  private initialized = false;

  async initialize(): Promise<void> {
    if (this.initialized) return;

    try {
      const vision = await FilesetResolver.forVisionTasks("/wasm");

      this.faceLandmarker = await FaceLandmarker.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath: "/models/face_landmarker.task",
          delegate: "GPU",
        },
        runningMode: "VIDEO",
        numFaces: 1,
        outputFaceBlendshapes: true,
        outputFacialTransformationMatrixes: true,
      });

      this.initialized = true;
      console.log("FaceDetector: FaceLandmarker initialized (VIDEO mode, local WASM)");
    } catch (error) {
      console.error("FaceDetector: initialization failed:", error);
      throw error;
    }
  }

  /**
   * Detect face from an HTMLVideoElement directly (optimal path — no extra copies).
   */
  detectFromVideo(video: HTMLVideoElement): FaceDetectionResult | null {
    if (!this.initialized || !this.faceLandmarker) return null;
    if (video.readyState < 2) return null; // not enough data

    try {
      const result = this.faceLandmarker.detectForVideo(video, performance.now());
      return this.processResult(result);
    } catch (error) {
      console.error("FaceDetector: detection error:", error);
      return null;
    }
  }

  /**
   * Fallback: detect from ImageData (used by calibration / still image paths).
   */
  async detectFace(imageData: ImageData): Promise<FaceDetectionResult | null> {
    if (!this.initialized || !this.faceLandmarker) {
      await this.initialize();
    }

    try {
      const canvas = document.createElement("canvas");
      canvas.width = imageData.width;
      canvas.height = imageData.height;
      const ctx = canvas.getContext("2d")!;
      ctx.putImageData(imageData, 0, 0);

      const result = this.faceLandmarker!.detectForVideo(canvas, performance.now());
      return this.processResult(result);
    } catch (error) {
      console.error("FaceDetector: ImageData detection error:", error);
      return null;
    }
  }

  // ────────── Result Processing ──────────

  private processResult(result: FaceLandmarkerResult): FaceDetectionResult | null {
    if (!result.faceLandmarks || result.faceLandmarks.length === 0) return null;

    const raw = result.faceLandmarks[0];
    if (!raw || raw.length < 468) return null;

    // Scale normalized coords → 320×240 canonical space
    const W = 320, H = 240;
    const landmarks: number[][] = raw.map((p) => [p.x * W, p.y * H, (p.z || 0) * W]);

    // Extract raw blendshapes map
    const blendshapes = this.extractBlendshapes(result);

    // Map blendshapes → our 6-AU schema (for backward compatibility with existing stores)
    const actionUnits = this.blendshapesToAU(blendshapes);

    const headPose  = this.computeHeadPose(landmarks);
    const eyeContact = this.computeEyeContact(landmarks);

    // Confidence from bounding box area
    const xs = raw.map((p) => p.x);
    const ys = raw.map((p) => p.y);
    const area = (Math.max(...xs) - Math.min(...xs)) * (Math.max(...ys) - Math.min(...ys));
    const confidence = area > 0.01 ? 0.9 : 0.5;

    return { confidence, landmarks, actionUnits, headPose, eyeContact, blendshapes };
  }

  /**
   * Extract all 52 blendshapes into a flat Record<name, score>.
   */
  private extractBlendshapes(result: FaceLandmarkerResult): Record<string, number> {
    const map: Record<string, number> = {};
    if (result.faceBlendshapes?.[0]?.categories) {
      for (const cat of result.faceBlendshapes[0].categories) {
        map[cat.categoryName] = cat.score;
      }
    }
    return map;
  }

  /**
   * Map MediaPipe blendshapes → backward-compatible AU1/4/6/12/15/25.
   */
  private blendshapesToAU(bs: Record<string, number>): Record<string, number> {
    const g = (k: string) => bs[k] || 0;
    return {
      AU1:  +Math.min(1, g("browInnerUp")).toFixed(3),
      AU4:  +Math.min(1, (g("browDownLeft") + g("browDownRight")) / 2).toFixed(3),
      AU6:  +Math.min(1, (g("cheekSquintLeft") + g("cheekSquintRight")) / 2).toFixed(3),
      AU12: +Math.min(1, (g("mouthSmileLeft") + g("mouthSmileRight")) / 2).toFixed(3),
      AU15: +Math.min(1, (g("mouthFrownLeft") + g("mouthFrownRight")) / 2).toFixed(3),
      AU25: +Math.min(1, Math.max(g("jawOpen"), g("mouthOpen") || 0)).toFixed(3),
    };
  }

  // ────────── Geometry Helpers ──────────

  private computeHeadPose(lm: number[][]): { pitch: number; yaw: number; roll: number } {
    const nose = lm[1], lc = lm[234], rc = lm[454], nr = lm[168];
    const cw = Math.abs(lc[0] - rc[0]);
    const cx = (lc[0] + rc[0]) / 2;
    return {
      pitch: Math.round(((nose[1] - nr[1]) / (cw || 1)) * 90 - 10),
      yaw:   Math.round(((nose[0] - cx)    / (cw || 1)) * 90),
      roll:  Math.round(Math.atan2(rc[1] - lc[1], rc[0] - lc[0]) * (180 / Math.PI)),
    };
  }

  private computeEyeContact(lm: number[][]): boolean {
    const li = lm[468], ri = lm[473];
    if (!li || !ri) return false;
    const lx = (lm[133][0] + lm[33][0]) / 2;
    const rx = (lm[362][0] + lm[263][0]) / 2;
    const ln = Math.abs(li[0] - lx) / Math.abs(lm[133][0] - lm[33][0]);
    const rn = Math.abs(ri[0] - rx) / Math.abs(lm[362][0] - lm[263][0]);
    return ln < 0.15 && rn < 0.15;
  }

  async dispose(): Promise<void> {
    if (this.faceLandmarker) {
      this.faceLandmarker.close();
      this.faceLandmarker = null;
      this.initialized = false;
    }
  }
}
