/**
 * Kalman Filter for smoothing emotion confidence signals.
 * Reduces jitter and stabilizes telemetry output.
 */
export class KalmanFilter {
  private state: number;
  private estimateError: number;
  private q: number; // Process noise
  private r: number; // Measurement noise

  constructor(
    initialState = 0,
    estimateError = 1,
    processNoise = 0.02,
    measurementNoise = 0.15
  ) {
    this.state = initialState;
    this.estimateError = estimateError;
    this.q = processNoise;
    this.r = measurementNoise;
  }

  /**
   * Filter a raw measurement signal
   */
  filter(measurement: number): number {
    // Prediction Update
    const predictionError = this.estimateError + this.q;

    // Measurement Update (Kalman Gain)
    const kalmanGain = predictionError / (predictionError + this.r);
    this.state = this.state + kalmanGain * (measurement - this.state);
    this.estimateError = (1 - kalmanGain) * predictionError;

    return this.state;
  }

  reset(initialState = 0): void {
    this.state = initialState;
    this.estimateError = 1;
  }
}
