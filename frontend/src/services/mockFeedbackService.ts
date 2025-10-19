/**
 * Mock Feedback Service
 * 
 * Provides mock feedback for testing without backend integration.
 * Simulates pose comparison results and feedback generation.
 */

export interface MockFeedbackResponse {
  timestamp: number;
  pose_landmarks: number[][] | null;
  hand_landmarks: number[][][];
  hand_classifications: Array<{
    gesture: string;
    confidence: number;
  }>;
  preprocessed_angles: Record<string, number>;
  comparison_result: {
    combined_score: number;
    pose_score: number;
    motion_score: number;
    dtw_score: number;
    best_match_idx: number;
    dtw_path: any[];
    timestamp: number;
  } | null;
  live_feedback: string | null;
  success: boolean;
  error?: string;
}

export interface MockFeedbackOptions {
  baseScore?: number;
  scoreVariation?: number;
  feedbackFrequency?: number; // 0-1, how often to provide feedback
  includeErrors?: boolean;
}

class MockFeedbackService {
  private frameCount = 0;
  private lastFeedbackTime = 0;
  private feedbackMessages = [
    "Great form! Keep it up!",
    "Try to raise your arms a bit higher",
    "Perfect timing with the beat!",
    "Bend your knees slightly more",
    "Excellent posture!",
    "Move your hips to the rhythm",
    "Keep your shoulders relaxed",
    "Great energy! Keep dancing!",
    "Try to match the reference more closely",
    "You're doing amazing!",
    "Focus on your arm positioning",
    "Great footwork!",
    "Keep the energy up!",
    "Try to stay in sync with the music",
    "Excellent dance moves!"
  ];

  private errorMessages = [
    { joint: "left_elbow", message: "Raise left elbow ~12° higher", severity: "medium" },
    { joint: "right_arm", message: "Extend right arm more", severity: "low" },
    { joint: "left_knee", message: "Bend left knee slightly more", severity: "high" },
    { joint: "right_hip", message: "Move right hip to the beat", severity: "medium" },
    { joint: "shoulders", message: "Keep shoulders more relaxed", severity: "low" }
  ];

  /**
   * Generate mock feedback response
   */
  generateMockFeedback(
    imageData: string, 
    options: MockFeedbackOptions = {}
  ): MockFeedbackResponse {
    const {
      baseScore = 0.75,
      scoreVariation = 0.2,
      feedbackFrequency = 0.3,
      includeErrors = true
    } = options;

    this.frameCount++;

    // Generate scores with some variation
    const poseScore = Math.max(0, Math.min(1, baseScore + (Math.random() - 0.5) * scoreVariation));
    const motionScore = Math.max(0, Math.min(1, poseScore + (Math.random() - 0.5) * 0.3));
    const combinedScore = (poseScore * 0.7 + motionScore * 0.3);

    // Decide whether to provide feedback
    const shouldProvideFeedback = Math.random() < feedbackFrequency;
    let liveFeedback: string | null = null;

    if (shouldProvideFeedback) {
      if (combinedScore > 0.8) {
        // Positive feedback for good scores
        liveFeedback = this.feedbackMessages[Math.floor(Math.random() * 5)];
      } else if (combinedScore < 0.6 && includeErrors) {
        // Corrective feedback for lower scores
        const error = this.errorMessages[Math.floor(Math.random() * this.errorMessages.length)];
        liveFeedback = error.message;
      } else {
        // General encouragement
        liveFeedback = this.feedbackMessages[Math.floor(Math.random() * this.feedbackMessages.length)];
      }
    }

    // Generate mock pose landmarks (simplified)
    const poseLandmarks = this.generateMockPoseLandmarks();
    const handLandmarks = this.generateMockHandLandmarks();
    const handClassifications = this.generateMockHandClassifications();

    // Generate mock angles
    const preprocessedAngles = this.generateMockAngles();

    const response: MockFeedbackResponse = {
      timestamp: Date.now(),
      pose_landmarks: poseLandmarks,
      hand_landmarks: handLandmarks,
      hand_classifications: handClassifications,
      preprocessed_angles: preprocessedAngles,
      comparison_result: {
        combined_score: combinedScore,
        pose_score: poseScore,
        motion_score: motionScore,
        dtw_score: combinedScore * 0.9, // Slightly lower DTW score
        best_match_idx: Math.floor(Math.random() * 50),
        dtw_path: [],
        timestamp: Date.now()
      },
      live_feedback: liveFeedback,
      success: true
    };

    return response;
  }

  /**
   * Generate mock pose landmarks
   */
  private generateMockPoseLandmarks(): number[][] {
    const landmarks: number[][] = [];
    
    // Generate 33 pose landmarks with some realistic variation
    for (let i = 0; i < 33; i++) {
      landmarks.push([
        Math.random() * 0.8 + 0.1, // x: 0.1 to 0.9
        Math.random() * 0.8 + 0.1, // y: 0.1 to 0.9
        Math.random() * 0.2 - 0.1, // z: -0.1 to 0.1
        Math.random() * 0.3 + 0.7  // visibility: 0.7 to 1.0
      ]);
    }
    
    return landmarks;
  }

  /**
   * Generate mock hand landmarks
   */
  private generateMockHandLandmarks(): number[][][] {
    const hands: number[][][] = [];
    
    // Generate 0-2 hands with some probability
    const numHands = Math.random() < 0.8 ? (Math.random() < 0.7 ? 2 : 1) : 0;
    
    for (let h = 0; h < numHands; h++) {
      const hand: number[][] = [];
      
      // Generate 21 hand landmarks
      for (let i = 0; i < 21; i++) {
        hand.push([
          Math.random() * 0.6 + 0.2, // x: 0.2 to 0.8
          Math.random() * 0.6 + 0.2, // y: 0.2 to 0.8
          Math.random() * 0.2 - 0.1  // z: -0.1 to 0.1
        ]);
      }
      
      hands.push(hand);
    }
    
    return hands;
  }

  /**
   * Generate mock hand classifications
   */
  private generateMockHandClassifications(): Array<{ gesture: string; confidence: number }> {
    const gestures = ['open_palm', 'closed_fist', 'pointing', 'peace_sign', 'thumbs_up'];
    const classifications: Array<{ gesture: string; confidence: number }> = [];
    
    // Generate 0-2 hand classifications
    const numHands = Math.random() < 0.8 ? (Math.random() < 0.7 ? 2 : 1) : 0;
    
    for (let i = 0; i < numHands; i++) {
      classifications.push({
        gesture: gestures[Math.floor(Math.random() * gestures.length)],
        confidence: Math.random() * 0.4 + 0.6 // 0.6 to 1.0
      });
    }
    
    return classifications;
  }

  /**
   * Generate mock preprocessed angles
   */
  private generateMockAngles(): Record<string, number> {
    return {
      left_elbow_bend: Math.random() * 60 + 90,     // 90-150 degrees
      right_elbow_bend: Math.random() * 60 + 90,    // 90-150 degrees
      left_knee_bend: Math.random() * 40 + 140,     // 140-180 degrees
      right_knee_bend: Math.random() * 40 + 140,    // 140-180 degrees
      left_shoulder_hip_angle: Math.random() * 30 + 15, // 15-45 degrees
      right_shoulder_hip_angle: Math.random() * 30 + 15, // 15-45 degrees
    };
  }

  /**
   * Simulate API delay
   */
  async simulateApiDelay(minMs: number = 50, maxMs: number = 200): Promise<void> {
    const delay = Math.random() * (maxMs - minMs) + minMs;
    await new Promise(resolve => setTimeout(resolve, delay));
  }

  /**
   * Process snapshot with mock feedback (async version)
   */
  async processSnapshot(
    imageData: string, 
    options: MockFeedbackOptions = {}
  ): Promise<MockFeedbackResponse> {
    // Simulate API delay
    await this.simulateApiDelay();
    
    return this.generateMockFeedback(imageData, options);
  }

  /**
   * Reset the service state
   */
  reset(): void {
    this.frameCount = 0;
    this.lastFeedbackTime = 0;
  }

  /**
   * Get service statistics
   */
  getStats(): { frameCount: number; averageScore: number } {
    return {
      frameCount: this.frameCount,
      averageScore: 0.75 // Mock average
    };
  }
}

// Export singleton config
export const mockFeedbackService = new MockFeedbackService();
