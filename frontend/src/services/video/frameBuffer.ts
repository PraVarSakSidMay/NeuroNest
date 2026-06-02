/**
 * Frame Buffer - bounded queue to store recent processed frames for analysis
 */
export class FrameBuffer {
  private buffer: ImageData[] = [];
  private maxSize: number;
  private dropPolicy: "oldest" | "newest" = "oldest";

  constructor(maxSize = 30) {
    this.maxSize = maxSize;
  }

  /**
   * Add frame to buffer (auto-drops oldest if full)
   */
  push(frame: ImageData): void {
    if (this.buffer.length >= this.maxSize) {
      if (this.dropPolicy === "oldest") {
        this.buffer.shift();
      } else {
        this.buffer.pop();
      }
    }
    this.buffer.push(frame);
  }

  /**
   * Get last N frames for temporal analysis
   */
  getLastN(count: number): ImageData[] {
    return this.buffer.slice(Math.max(0, this.buffer.length - count));
  }

  /**
   * Clear buffer (for cleanup or reset)
   */
  clear(): void {
    this.buffer = [];
  }

  /**
   * Get buffer stats
   */
  stats() {
    return {
      size: this.buffer.length,
      maxSize: this.maxSize,
      memoryUsage: `${(this.buffer.length * 320 * 240 * 4) / 1024}KB`,
    };
  }
}
