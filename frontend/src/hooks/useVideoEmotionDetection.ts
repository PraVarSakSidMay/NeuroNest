/**
 * useVideoEmotionDetection hook - coordinates camera video feed,
 * MediaPipe FaceLandmarker detection, blendshape-based emotion classification,
 * and multimodal fusion.
 */
import { useEffect, useRef, useState } from "react";
import * as faceapi from "@vladmandic/face-api";
import { VideoCaptureManager } from "../services/video/videoCaptureManager";
import { FaceDetector } from "../services/video/faceDetector";
import { EmotionClassifier } from "../services/video/emotionClassifier";
import { MultimodalFusionEngine } from "../services/fusion/multimodalFusion";
import { KalmanFilter } from "../services/filtering/kalmanFilter";
import { EmotionSmoother } from "../services/filtering/emotionSmoothing";
import { PrivacyManager } from "../services/privacy/privacyManager";
import { useEmotionStore } from "../stores/useEmotionStore";
import { useConversationStore } from "../stores/useConversationStore";
import { useVoiceStore } from "../stores/useVoiceStore";

export function useVideoEmotionDetection(
  videoRef: React.RefObject<HTMLVideoElement | null>,
  canvasRef?: React.RefObject<HTMLCanvasElement | null>,
  enabled = true
) {
  const [fps, setFps] = useState(0);

  const captureManagerRef = useRef<VideoCaptureManager | null>(null);
  const faceDetectorRef = useRef<FaceDetector | null>(null);
  const classifierRef = useRef<EmotionClassifier | null>(null);
  const fusionEngineRef = useRef<MultimodalFusionEngine | null>(null);
  const kalmanFilterRef = useRef<KalmanFilter | null>(null);
  const smootherRef = useRef<EmotionSmoother | null>(null);
  const privacyRef = useRef<PrivacyManager | null>(null);

  // Frame buffer ref for calibration
  const calibrationFramesRef = useRef<Record<string, number>[]>([]);

  const {
    setVideoEmotion,
    setFusedEmotion,
    setFaceQuality,
    setTrackingStatus,
    setFps: setStoreFps,
    setCameraActive,
    trackingStatus,
    setNeutralBaseline,
    setEyeContact,
    setHeadPose,
    addEyeContactHistory,
    addExpressionHistory,
  } = useEmotionStore();

  // Get current voice features and previous turn's emotion to feed into client-side fusion
  const { audioFeatures } = useVoiceStore();
  const { emotion: lastContextEmotion } = useConversationStore();

  useEffect(() => {
    if (!enabled || !videoRef.current) {
      setTrackingStatus("off");
      setCameraActive(false);
      
      // Clear canvas on disable
      if (canvasRef?.current) {
        const ctx = canvasRef.current.getContext("2d");
        ctx?.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
      }
      return;
    }

    let stopCaptureFn: (() => void) | null = null;
    let frameCount = 0;
    let lastTime = Date.now();
    let isDisposed = false;

    const setupDetection = async () => {
      try {
        setTrackingStatus("loading");
        setCameraActive(true);

        // Instantiate services
        captureManagerRef.current = new VideoCaptureManager();
        faceDetectorRef.current = new FaceDetector();
        classifierRef.current = new EmotionClassifier();
        fusionEngineRef.current = new MultimodalFusionEngine();
        kalmanFilterRef.current = new KalmanFilter();
        smootherRef.current = new EmotionSmoother();
        privacyRef.current = new PrivacyManager();

        // Initialize camera stream and MediaPipe FaceLandmarker
        await captureManagerRef.current.initialize(videoRef.current!);
        await faceDetectorRef.current.initialize();

        // Load face-api models from CDN
        try {
          const MODEL_CDN_URL = "https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model";
          await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_CDN_URL);
          await faceapi.nets.faceExpressionNet.loadFromUri(MODEL_CDN_URL);
          console.log("useVideoEmotionDetection: face-api.js models initialized from CDN");
        } catch (err) {
          console.error("useVideoEmotionDetection: Failed to load face-api models:", err);
        }

        // Load baseline from localStorage if it exists
        try {
          const storedBaseline = localStorage.getItem("face_neutral_baseline");
          if (storedBaseline) {
            setNeutralBaseline(JSON.parse(storedBaseline));
          }
        } catch (err) {
          console.warn("Failed to load baseline from localStorage:", err);
        }

        if (isDisposed) return;
        setTrackingStatus("tracking");

        // Start detection loop at ~5 FPS using direct video element feed
        // (no ImageData round-trip — detectFromVideo feeds HTMLVideoElement directly)
        const DETECTION_INTERVAL = 200; // ms = 5 FPS
        let processing = false;

        const detectionLoop = setInterval(async () => {
          if (isDisposed || !faceDetectorRef.current || !classifierRef.current || !videoRef.current) return;
          if (processing) return;
          processing = true;

          try {
            // 1. Detect face directly from video element (optimal path)
            const faceResult = faceDetectorRef.current.detectFromVideo(videoRef.current);

            // Clear previous canvas drawing
            if (canvasRef?.current) {
              const ctx = canvasRef.current.getContext("2d");
              if (ctx) {
                ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
              }
            }

            if (!faceResult) {
              setTrackingStatus("no-face");
              setVideoEmotion(null);
              setFusedEmotion(null);
              return;
            }

            setTrackingStatus("tracking");

            // Update head pose and eye contact states in store
            setEyeContact(faceResult.eyeContact);
            setHeadPose(faceResult.headPose);

            // If voice recording is active, append to eye contact history buffer
            if (useVoiceStore.getState().isRecording) {
              addEyeContactHistory(faceResult.eyeContact);
            }

            // Draw landmarks on the overlay canvas locally (never transmitted)
            if (canvasRef?.current && faceResult.landmarks) {
              const ctx = canvasRef.current.getContext("2d");
              if (ctx) {
                const width = canvasRef.current.width;
                const height = canvasRef.current.height;
                for (let i = 0; i < faceResult.landmarks.length; i++) {
                  const [x, y] = faceResult.landmarks[i];
                  // Scale from 320x240 image space to actual canvas dimensions
                  const scaledX = (x / 320) * width;
                  const scaledY = (y / 240) * height;

                  ctx.beginPath();
                  if (i >= 468) {
                    // Iris landmarks in glowing violet
                    ctx.fillStyle = "rgba(168, 85, 247, 0.95)";
                    ctx.arc(scaledX, scaledY, 1.5, 0, 2 * Math.PI);
                  } else {
                    // Standard Facemesh points in neon cyan
                    ctx.fillStyle = "rgba(34, 211, 238, 0.75)";
                    ctx.arc(scaledX, scaledY, 1.0, 0, 2 * Math.PI);
                  }
                  ctx.fill();
                }
              }
            }

            const storeState = useEmotionStore.getState();
            const currentIsCalibrating = storeState.isCalibrating;
            const currentNeutralBaseline = storeState.neutralBaseline;

            // If calibrating, accumulate Action Units and bypass standard emotion classification
            if (currentIsCalibrating) {
              calibrationFramesRef.current.push(faceResult.actionUnits);
              const count = calibrationFramesRef.current.length;
              const progress = Math.min(100, Math.round((count / 15) * 100)); // 15 frames = ~3 seconds at 5 FPS
              storeState.setCalibrationProgress(progress);

              if (progress >= 100) {
                const accumulated = calibrationFramesRef.current;
                const keys = ["AU1", "AU4", "AU6", "AU12", "AU15", "AU25"];
                const averages: Record<string, number> = {};

                keys.forEach((key) => {
                  const sum = accumulated.reduce((s, f) => s + (f[key] || 0), 0);
                  averages[key] = parseFloat((sum / accumulated.length).toFixed(3));
                });

                storeState.setNeutralBaseline(averages);
                storeState.setIsCalibrating(false);
                try {
                  localStorage.setItem("face_neutral_baseline", JSON.stringify(averages));
                } catch (e) {
                  console.warn("Failed to persist baseline:", e);
                }
                calibrationFramesRef.current = [];
              }

              setVideoEmotion({
                emotion: "neutral",
                confidence: 1.0,
                actionUnits: faceResult.actionUnits,
              });

              setFusedEmotion({
                emotion: "neutral",
                confidence: 1.0,
                isMasked: false,
                maskConfidence: 0,
                recommendation: "Calibrating baseline... Please hold still.",
              });
              return;
            }

            // Normalize Action Units if neutral baseline is loaded
            let processedActionUnits = faceResult.actionUnits;
            if (currentNeutralBaseline) {
              processedActionUnits = {};
              for (const [key, rawVal] of Object.entries(faceResult.actionUnits)) {
                const baselineVal = currentNeutralBaseline[key] || 0;
                const normalizedVal = Math.max(0, rawVal - baselineVal) / Math.max(0.01, 1.0 - baselineVal);
                processedActionUnits[key] = parseFloat(normalizedVal.toFixed(3));
              }
            }

            // 1b. Detect face expressions asynchronously with face-api.js
            let faceApiExpressions: Record<string, number> | undefined = undefined;
            try {
              if (faceapi.nets.faceExpressionNet.isLoaded && faceapi.nets.tinyFaceDetector.isLoaded) {
                const faceapiRes = await faceapi.detectSingleFace(
                  videoRef.current,
                  new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.5 })
                ).withFaceExpressions();

                if (faceapiRes && faceapiRes.expressions) {
                  faceApiExpressions = faceapiRes.expressions as unknown as Record<string, number>;
                }
              }
            } catch (err) {
              console.warn("useVideoEmotionDetection: face-api.js detection failed:", err);
            }

            // 2. Classify face emotion using rich blendshapes (52 features) and face-api.js deep learning anchoring
            const rawPred = classifierRef.current.classifyEmotion(
              processedActionUnits,
              faceResult.eyeContact,
              faceResult.headPose,
              faceResult.blendshapes,  // pass full 52-blendshape map for accurate classification
              faceApiExpressions
            );

            // 3. Smooth confidence scoring via Kalman filter and EMA
            const kalmanConfidence = kalmanFilterRef.current!.filter(rawPred.confidence);
            const smoothed = smootherRef.current!.smoothEmotion(rawPred.emotion, kalmanConfidence);

            if (useVoiceStore.getState().isRecording) {
              classifierRef.current?.recordExpression(smoothed.smoothedEmotion);
              addExpressionHistory({
                emotion: smoothed.smoothedEmotion,
                confidence: smoothed.smoothedConfidence,
                timestamp: Date.now(),
                source: "video",
                face_quality: faceResult.confidence,
                eye_contact: faceResult.eyeContact,
                head_pose: faceResult.headPose,
                action_units: processedActionUnits,
              });
            }
            setVideoEmotion({
              emotion: smoothed.smoothedEmotion,
              confidence: smoothed.smoothedConfidence,
              actionUnits: processedActionUnits,
            });

            setFaceQuality(faceResult.confidence);

            // 5. Run Multimodal Fusion combining voice features and conversation history
            const fusionResult = fusionEngineRef.current!.fuseEmotions(
              { emotion: smoothed.smoothedEmotion, confidence: smoothed.smoothedConfidence },
              audioFeatures,
              lastContextEmotion?.emotion || "neutral"
            );

            setFusedEmotion({
              emotion: fusionResult.emotion,
              confidence: fusionResult.confidence,
              isMasked: fusionResult.isMasked,
              maskConfidence: fusionResult.maskConfidence,
              recommendation: fusionResult.recommendation,
            });

            // 6. Track FPS
            frameCount++;
            const now = Date.now();
            if (now - lastTime >= 1000) {
              const calculatedFps = Math.round((frameCount * 1000) / (now - lastTime));
              setFps(calculatedFps);
              setStoreFps(calculatedFps);
              frameCount = 0;
              lastTime = now;
            }
          } finally {
            processing = false;
          }
        }, DETECTION_INTERVAL);

        // Store cleanup function
        stopCaptureFn = () => clearInterval(detectionLoop);
      } catch (error) {
        console.error("Failed to initialize video emotion detection:", error);
        if (!isDisposed) {
          setTrackingStatus("error");
          setCameraActive(false);
        }
      }
    };

    setupDetection();

    return () => {
      isDisposed = true;
      setCameraActive(false);
      setTrackingStatus("off");
      setVideoEmotion(null);
      setFusedEmotion(null);

      if (stopCaptureFn) {
        stopCaptureFn();
      }

      // Clear canvas on cleanup
      if (canvasRef?.current) {
        const ctx = canvasRef.current.getContext("2d");
        ctx?.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
      }

      const disposeResources = async () => {
        if (captureManagerRef.current) {
          await captureManagerRef.current.dispose();
          captureManagerRef.current = null;
        }
        if (faceDetectorRef.current) {
          await faceDetectorRef.current.dispose();
          faceDetectorRef.current = null;
        }
        classifierRef.current = null;
        fusionEngineRef.current = null;
        kalmanFilterRef.current = null;
        smootherRef.current = null;
        privacyRef.current = null;
      };
      disposeResources();
    };
  }, [enabled, videoRef, videoRef.current, canvasRef, canvasRef.current, audioFeatures, lastContextEmotion, setVideoEmotion, setFusedEmotion, setFaceQuality, setTrackingStatus, setStoreFps, setCameraActive]);

  return { fps, trackingStatus };
}
