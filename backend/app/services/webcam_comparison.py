"""
Real-time webcam comparison with test_poses.npy
Shows live comparison scores on the video feed
"""

import cv2
import numpy as np
import mediapipe as mp
import time
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pose_comparison_service import PoseComparisonService

def main():
    """Main function for real-time webcam comparison"""
    print("🎯 Real-Time Pose Comparison with test.MOV")
    print("=" * 60)

    # Load reference data
    print("\n1. Loading Reference Data:")
    try:
        # Get correct path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_file = os.path.join(current_dir, "..", "data", "processed_poses", "test_poses.npy")

        if not os.path.exists(data_file):
            print(f"❌ File not found: {data_file}")
            return
        
        # Load the data
        data = np.load(data_file, allow_pickle=True)
        print(f"✅ Loaded {len(data)} reference poses")
        
        # Convert to format expected by PoseComparisonService
        reference_poses_list = []
        for frame_data in data:
            if frame_data.get('has_pose', False):
                pose_dict = {
                    'landmarks': frame_data['landmarks'],
                    'timestamp': frame_data['timestamp'],
                    'frame_number': frame_data['frame_number']
                }
                reference_poses_list.append(pose_dict)
        
        print(f"✅ Converted {len(reference_poses_list)} poses for comparison")
        
        # Initialize comparison service
        comparison_service = PoseComparisonService(reference_poses_list)
        print("✅ Comparison service initialized")
        
    except Exception as e:
        print(f"❌ Error loading reference data: {e}")
        return
    
    # Initialize MediaPipe
    print("\n2. Initializing MediaPipe:")
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    print("✅ MediaPipe initialized")
    
    # Open webcam
    print("\n3. Opening Webcam:")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Cannot open webcam")
        return
    
    # Set webcam properties for better performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    print("✅ Webcam opened")
    
    # Countdown before starting
    print("\n⏰ Get ready! Starting in...")
    for i in range(5, 0, -1):
        print(f"   {i}...")
        
        # Show countdown on screen
        ret, frame = cap.read()
        if ret:
            # Black background
            cv2.rectangle(frame, (0, 0), (640, 480), (0, 0, 0), -1)
            
            # Big countdown number
            text = str(i)
            font = cv2.FONT_HERSHEY_SIMPLEX
            text_size = cv2.getTextSize(text, font, 5, 10)[0]
            text_x = (640 - text_size[0]) // 2
            text_y = (480 + text_size[1]) // 2
            cv2.putText(frame, text, (text_x, text_y), font, 5, (255, 255, 255), 10)
            
            # Instructions
            cv2.putText(frame, "Get into position!", (180, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.putText(frame, "Comparison starting in...", (160, 380), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
            
            cv2.imshow('Pose Comparison - Press q to quit', frame)
            cv2.waitKey(1000)  # Wait 1 second
        else:
            time.sleep(1)
    
    print("\n📸 Starting real-time comparison NOW!")
    print("Press 'q' to quit, 'r' to reset scores")
    print("-" * 60)
    
    # Statistics tracking
    frame_count = 0
    poses_detected = 0
    avg_score = 0
    max_score = 0
    scores_history = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to read from webcam")
            break
        
        frame_count += 1
        
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process pose
        results = pose.process(rgb_frame)
        
        # Initialize display text
        comparison_text = "No pose detected"
        score_color = (0, 0, 255)  # Red by default
        
        if results.pose_landmarks:
            poses_detected += 1
            
            # Draw pose landmarks
            mp_drawing.draw_landmarks(
                frame, 
                results.pose_landmarks, 
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=2)
            )
            
            # Convert landmarks to numpy array
            pose_landmarks = np.array([[lm.x, lm.y, lm.z, lm.visibility] 
                                      for lm in results.pose_landmarks.landmark])
            
            # Get comparison result
            try:
                comparison_result = comparison_service.update_user_pose(pose_landmarks)
                
                if comparison_result:
                    combined_score = float(comparison_result.get('combined_score', 0))
                    pose_score = float(comparison_result.get('pose_score', 0))
                    motion_score = float(comparison_result.get('motion_score', 0))
                    
                    # Update statistics
                    scores_history.append(combined_score)
                    if len(scores_history) > 30:  # Keep last 30 scores
                        scores_history.pop(0)
                    
                    avg_score = np.mean(scores_history)
                    max_score = max(max_score, combined_score)
                    
                    # Create comparison text
                    if motion_score > 0:
                        comparison_text = f"Score: {combined_score:.2f} | Pose: {pose_score:.2f} | Motion: {motion_score:.2f}"
                    else:
                        comparison_text = f"Score: {combined_score:.2f} | Pose: {pose_score:.2f} | Motion: Building..."
                    
                    # Color based on score
                    if combined_score >= 0.8:
                        score_color = (0, 255, 0)  # Green - Excellent
                    elif combined_score >= 0.6:
                        score_color = (0, 200, 255)  # Yellow - Good
                    elif combined_score >= 0.4:
                        score_color = (0, 165, 255)  # Orange - Decent
                    else:
                        score_color = (0, 0, 255)  # Red - Needs improvement
                        
            except Exception as e:
                comparison_text = f"Comparison error: {str(e)[:30]}"
        
        # Draw UI overlay
        # Background for text
        cv2.rectangle(frame, (0, 0), (640, 120), (0, 0, 0), -1)
        
        # Title
        cv2.putText(frame, "Real-Time Pose Comparison", (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Comparison score
        cv2.putText(frame, comparison_text, (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, score_color, 2)
        
        # Statistics
        stats_text = f"Avg: {avg_score:.2f} | Max: {max_score:.2f} | Detection: {poses_detected}/{frame_count}"
        cv2.putText(frame, stats_text, (10, 75), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Instructions
        cv2.putText(frame, "Press 'q' to quit, 'r' to reset", (10, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        
        # Score bar visualization
        if scores_history:
            bar_width = int(combined_score * 600)
            cv2.rectangle(frame, (20, 440), (620, 460), (50, 50, 50), -1)
            cv2.rectangle(frame, (20, 440), (20 + bar_width, 460), score_color, -1)
            cv2.rectangle(frame, (20, 440), (620, 460), (255, 255, 255), 2)
        
        # Show frame
        cv2.imshow('Pose Comparison - Press q to quit', frame)
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            # Reset statistics
            scores_history = []
            avg_score = 0
            max_score = 0
            poses_detected = 0
            frame_count = 0
            print("📊 Statistics reset")
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    pose.close()
    
    # Print final statistics
    print("\n" + "=" * 60)
    print("📊 Final Statistics:")
    print(f"   Total frames: {frame_count}")
    print(f"   Poses detected: {poses_detected}")
    print(f"   Detection rate: {poses_detected/frame_count*100:.1f}%" if frame_count > 0 else "   Detection rate: 0%")
    print(f"   Average score: {avg_score:.3f}")
    print(f"   Maximum score: {max_score:.3f}")
    print("\n✅ Comparison test completed!")

if __name__ == "__main__":
    main()
