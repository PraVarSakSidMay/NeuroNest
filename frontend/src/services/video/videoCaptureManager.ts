/**
 * Video Capture Manager - handles getUserMedia and frame extraction to Canvas.
 * Runs entirely in the browser.
 */
export class VideoCaptureManager {
  private videoRef: HTMLVideoElement | null = null;
  private canvasRef: HTMLCanvasElement | null = null;
  private stream: MediaStream | null = null;
  private frameRate = 30; // Capture at 30fps
  private processRate = 5; // Process 5fps (reduce CPU load)

  async initialize(videoElement: HTMLVideoElement): Promise<void> {
    this.videoRef = videoElement;
    this.canvasRef = document.createElement("canvas");

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 }, // Resize to smaller size directly at source if possible
          height: { ideal: 480 },
          facingMode: "user",
        },
        audio: false, // Audio handled separately
      });

      this.videoRef.srcObject = this.stream;
      await new Promise<void>((resolve) => {
        if (!this.videoRef) return resolve();
        this.videoRef.onloadedmetadata = () => {
          resolve();
        };
      });

      console.log("Video capture initialized");
    } catch (error) {
      console.error("Failed to initialize video:", error);
      throw error;
    }
  }

  /**
   * Extract frame and resize for processing
   */
  captureFrame(targetWidth = 320, targetHeight = 240): ImageData | null {
    if (!this.videoRef || !this.canvasRef || !this.stream) return null;
    if (this.videoRef.readyState < 2) return null; // Not enough data yet

    this.canvasRef.width = targetWidth;
    this.canvasRef.height = targetHeight;

    const ctx = this.canvasRef.getContext("2d");
    if (!ctx) return null;

    // Draw video frame to canvas (automatically resizes)
    ctx.drawImage(this.videoRef, 0, 0, targetWidth, targetHeight);

    // Return compressed frame data
    return ctx.getImageData(0, 0, targetWidth, targetHeight);
  }

  /**
   * Start continuous frame capture loop
   * Processes at specified rate (default 5fps for inference)
   */
  startCapture(onFrame: (imageData: ImageData) => void | Promise<void>): () => void {
    let isCapturing = true;
    const frameDuration = 1000 / this.processRate;

    const captureLoop = async () => {
      if (!isCapturing) return;

      const startTime = performance.now();
      const frame = this.captureFrame();

      if (frame && isCapturing) {
        try {
          await onFrame(frame);
        } catch (error) {
          console.error("Capture loop onFrame error:", error);
        }
      }

      const elapsed = performance.now() - startTime;
      const delay = Math.max(0, frameDuration - elapsed);

      if (isCapturing) {
        setTimeout(captureLoop, delay);
      }
    };

    // Run first loop
    captureLoop();

    // Return cleanup function
    return () => {
      isCapturing = false;
    };
  }

  /**
   * Get current video stream info (for stats/debugging)
   */
  getStreamStats() {
    if (!this.stream) return null;

    const videoTrack = this.stream.getVideoTracks()[0];
    const settings = videoTrack?.getSettings();

    return {
      width: settings?.width,
      height: settings?.height,
      frameRate: settings?.frameRate,
      facingMode: settings?.facingMode,
    };
  }

  /**
   * Cleanup resources
   */
  async dispose(): Promise<void> {
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }
    if (this.videoRef) {
      this.videoRef.srcObject = null;
      this.videoRef = null;
    }
    this.canvasRef = null;
  }
}
