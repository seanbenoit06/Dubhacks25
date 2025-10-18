import cv2
import numpy as np
import mediapipe as mp
import time
import threading
import os
from typing import Optional, Dict, Any
import subprocess
import sys
import tempfile

# Try to import simpleaudio, install if not available
try:
    import simpleaudio as sa
    AUDIO_AVAILABLE = True
except ImportError:
    print("simpleaudio not available. Install with: pip install simpleaudio")
    AUDIO_AVAILABLE = False

# Try to import pydub for audio extraction
try:
    from pydub import AudioSegment
    from pydub.utils import which
    PYDUB_AVAILABLE = True
except ImportError:
    print("pydub not available. Install with: pip install pydub")
    PYDUB_AVAILABLE = False

from pose_comparison_service import PoseComparisonService
from process_video_pose import VideoPoseProcessor

class SyncTestInterface:
    """
    Synchronized test interface that displays reference video and live webcam feed side-by-side.
    Includes audio support and pose comparison visualization.
    """
    
    def __init__(self, reference_video_path: str, reference_audio_path: Optional[str] = None):
        """
        Initialize the synchronized test interface.
        
        Args:
            reference_video_path: Path to the reference video file
            reference_audio_path: Optional path to audio file (if different from video)
        """
        self.reference_video_path = reference_video_path
        self.reference_audio_path = reference_audio_path or reference_video_path
        
        # Video properties
        self.video_cap = None
        self.webcam_cap = None
        self.video_fps = 30.0
        self.webcam_fps = 30.0
        self.video_duration = 0.0
        
        # Audio properties
        self.extracted_audio_path = None
        self.audio_duration = 0.0
        
        # Display properties
        self.display_width = 1280
        self.display_height = 720
        self.video_width = 640
        self.video_height = 480
        
        # State management
        self.is_running = False
        self.is_playing = False
        self.countdown_active = False
        self.countdown_value = 5
        
        # MediaPipe initialization
        self.mp_pose = mp.solutions.pose
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Pose comparison
        self.pose_comparison_service = None
        self.reference_poses_data = None
        
        # Audio
        self.audio_object = None
        self.audio_thread = None
        
        # Performance tracking
        self.frame_times = []
        self.last_frame_time = time.time()
        
        # Load reference pose data
        self._load_reference_poses()
        
        # Extract audio from video if needed
        self._extract_audio_from_video()
        
    def _load_reference_poses(self):
        """Load reference pose data from processed video."""
        try:
            # Check if processed pose data exists
            processor = VideoPoseProcessor()
            video_filename = os.path.basename(self.reference_video_path)
            base_name = os.path.splitext(video_filename)[0]
            poses_filename = f"{base_name}_poses.npy"
            
            if os.path.exists(os.path.join(processor.processed_poses_dir, poses_filename)):
                self.reference_poses_data = processor.load_processed_poses(poses_filename)
                self.pose_comparison_service = PoseComparisonService(self.reference_poses_data)
                print(f"Loaded reference poses: {len(self.reference_poses_data)} frames")
            else:
                print(f"Processed pose data not found for {video_filename}")
                print("Please run process_video_pose.py first to process the reference video.")
                
        except Exception as e:
            print(f"Error loading reference poses: {e}")
            self.reference_poses_data = None
            self.pose_comparison_service = None
    
    def _extract_audio_from_video(self):
        """Extract audio from video file and save as temporary WAV file."""
        if not PYDUB_AVAILABLE:
            print("pydub not available - cannot extract audio from video")
            return
        
        try:
            # Check if we need to extract audio (if reference_audio_path is the same as video)
            if self.reference_audio_path == self.reference_video_path:
                print("Extracting audio from video...")
                
                # Load video and extract audio
                video = AudioSegment.from_file(self.reference_video_path)
                
                # Create temporary WAV file
                temp_dir = tempfile.gettempdir()
                video_filename = os.path.splitext(os.path.basename(self.reference_video_path))[0]
                self.extracted_audio_path = os.path.join(temp_dir, f"{video_filename}_extracted_audio.wav")
                
                # Export audio as WAV
                video.export(self.extracted_audio_path, format="wav")
                
                # Get audio duration
                self.audio_duration = len(video) / 1000.0  # Convert milliseconds to seconds
                
                print(f"Audio extracted to: {self.extracted_audio_path}")
                print(f"Audio duration: {self.audio_duration:.2f} seconds")
                
                # Update reference_audio_path to use extracted audio
                self.reference_audio_path = self.extracted_audio_path
            else:
                # Audio file is separate, just get its duration
                if os.path.exists(self.reference_audio_path):
                    audio = AudioSegment.from_file(self.reference_audio_path)
                    self.audio_duration = len(audio) / 1000.0
                    print(f"Using separate audio file: {self.reference_audio_path}")
                    print(f"Audio duration: {self.audio_duration:.2f} seconds")
                
        except Exception as e:
            print(f"Error extracting audio: {e}")
            print("Audio will not be available")
            self.extracted_audio_path = None
            self.audio_duration = 0.0
    
    def _initialize_video(self):
        """Initialize video capture."""
        self.video_cap = cv2.VideoCapture(self.reference_video_path)
        if not self.video_cap.isOpened():
            raise IOError(f"Could not open video file: {self.reference_video_path}")
        
        self.video_fps = self.video_cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_duration = total_frames / self.video_fps if self.video_fps > 0 else 0
        
        print(f"Video FPS: {self.video_fps}")
        print(f"Video duration: {self.video_duration:.2f} seconds")
        print(f"Total frames: {total_frames}")
        
        # Set video position to start
        self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    def _initialize_webcam(self):
        """Initialize webcam capture."""
        self.webcam_cap = cv2.VideoCapture(0)
        if not self.webcam_cap.isOpened():
            raise IOError("Could not open webcam")
        
        # Set webcam properties
        self.webcam_cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.video_width)
        self.webcam_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.video_height)
        self.webcam_cap.set(cv2.CAP_PROP_FPS, self.webcam_fps)
        
        print(f"Webcam initialized: {self.video_width}x{self.video_height}")
    
    def _initialize_audio(self):
        """Initialize audio playback."""
        if not AUDIO_AVAILABLE:
            print("Audio not available - simpleaudio not installed")
            return
        
        try:
            # Load audio file (either extracted or separate)
            if os.path.exists(self.reference_audio_path):
                self.audio_object = sa.WaveObject.from_wave_file(self.reference_audio_path)
                print(f"Audio loaded: {self.reference_audio_path}")
                
                # Sync audio duration with video duration
                if self.audio_duration > 0 and self.video_duration > 0:
                    duration_diff = abs(self.audio_duration - self.video_duration)
                    if duration_diff > 0.5:  # More than 0.5 second difference
                        print(f"Warning: Audio duration ({self.audio_duration:.2f}s) differs from video duration ({self.video_duration:.2f}s)")
                        print(f"Difference: {duration_diff:.2f} seconds")
            else:
                print(f"Audio file not found: {self.reference_audio_path}")
                self.audio_object = None
                
        except Exception as e:
            print(f"Error initializing audio: {e}")
            self.audio_object = None
    
    def _play_audio(self):
        """Play audio in a separate thread."""
        if self.audio_object and AUDIO_AVAILABLE:
            try:
                play_obj = self.audio_object.play()
                play_obj.wait_done()
            except Exception as e:
                print(f"Error playing audio: {e}")
    
    def _resize_frame(self, frame, target_width, target_height):
        """Resize frame while maintaining aspect ratio."""
        height, width = frame.shape[:2]
        
        # Calculate scaling factor
        scale_w = target_width / width
        scale_h = target_height / height
        scale = min(scale_w, scale_h)
        
        # Calculate new dimensions
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        # Resize frame
        resized = cv2.resize(frame, (new_width, new_height))
        
        # Create black background
        background = np.zeros((target_height, target_width, 3), dtype=np.uint8)
        
        # Center the resized frame
        y_offset = (target_height - new_height) // 2
        x_offset = (target_width - new_width) // 2
        background[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = resized
        
        return background
    
    def _draw_countdown(self, frame, countdown_value):
        """Draw countdown overlay on frame."""
        height, width = frame.shape[:2]
        
        # Draw semi-transparent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, height), (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
        
        # Draw countdown text
        text = str(countdown_value) if countdown_value > 0 else "GO!"
        font_scale = 8 if countdown_value > 0 else 6
        color = (0, 255, 0) if countdown_value > 0 else (0, 0, 255)
        
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 10)[0]
        text_x = (width - text_size[0]) // 2
        text_y = (height + text_size[1]) // 2
        
        cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 
                   font_scale, color, 10)
        
        return frame
    
    def _draw_similarity_overlay(self, frame, similarity_data):
        """Draw pose similarity overlay on frame."""
        if not similarity_data:
            return frame
        
        # Draw semi-transparent background for text
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (300, 120), (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 0.8, overlay, 0.2, 0)
        
        # Draw similarity scores
        y_offset = 30
        cv2.putText(frame, f"Combined: {similarity_data['combined_score']:.3f}", 
                   (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y_offset += 25
        
        cv2.putText(frame, f"Pose: {similarity_data['pose_score']:.3f}", 
                   (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        y_offset += 20
        
        cv2.putText(frame, f"Motion: {similarity_data['motion_score']:.3f}", 
                   (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        y_offset += 20
        
        cv2.putText(frame, f"DTW: {similarity_data['dtw_score']:.3f}", 
                   (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        
        return frame
    
    def _process_webcam_frame(self, frame):
        """Process webcam frame for pose detection and comparison."""
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process with MediaPipe
        with self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as pose:
            
            pose_results = pose.process(frame_rgb)
            
            # Draw pose landmarks
            if pose_results.pose_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame,
                    pose_results.pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    self.mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=2)
                )
                
                # Update pose comparison if service is available
                if self.pose_comparison_service:
                    landmarks = np.array([[lm.x, lm.y, lm.z, lm.visibility] 
                                        for lm in pose_results.pose_landmarks.landmark])
                    
                    # Extract 3D coordinates and flatten
                    coords = landmarks[:, :3].flatten()
                    
                    similarity_data = self.pose_comparison_service.update_user_pose(coords)
                    frame = self._draw_similarity_overlay(frame, similarity_data)
        
        return frame
    
    def _countdown_loop(self):
        """Handle countdown before starting playback."""
        self.countdown_active = True
        self.countdown_value = 5
        
        while self.countdown_active and self.countdown_value > 0:
            time.sleep(1.0)
            self.countdown_value -= 1
        
        self.countdown_active = False
        self.is_playing = True
        
        # Start audio playback in separate thread
        if self.audio_object and AUDIO_AVAILABLE:
            self.audio_thread = threading.Thread(target=self._play_audio)
            self.audio_thread.daemon = True
            self.audio_thread.start()
    
    def run(self):
        """Main run loop for the synchronized test interface."""
        try:
            # Initialize components
            self._initialize_video()
            self._initialize_webcam()
            self._initialize_audio()
            
            # Create display window
            cv2.namedWindow('Synchronized Dance Test', cv2.WINDOW_AUTOSIZE)
            
            print("Synchronized Dance Test Interface")
            print("Press 's' to start countdown and begin playback")
            print("Press 'q' to quit")
            print("Press 'r' to reset")
            
            self.is_running = True
            countdown_thread = None
            
            # Video frame timing - ensure exact FPS timing
            frame_duration = 1.0 / self.video_fps
            video_start_time = None
            audio_start_time = None
            
            while self.is_running:
                current_time = time.time()
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    self.is_running = False
                    break
                elif key == ord('s') and not self.is_playing and not self.countdown_active:
                    print("Starting countdown...")
                    countdown_thread = threading.Thread(target=self._countdown_loop)
                    countdown_thread.daemon = True
                    countdown_thread.start()
                    # Reset timing variables
                    video_start_time = None
                    audio_start_time = None
                elif key == ord('r'):
                    # Reset playback
                    self.is_playing = False
                    self.countdown_active = False
                    if self.video_cap:
                        self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    video_start_time = None
                    audio_start_time = None
                    print("Reset playback")
                
                # Capture webcam frame
                webcam_success, webcam_frame = self.webcam_cap.read()
                if not webcam_success:
                    print("Failed to read from webcam")
                    break
                
                # Process webcam frame
                webcam_frame = self._process_webcam_frame(webcam_frame)
                webcam_frame = self._resize_frame(webcam_frame, self.video_width, self.video_height)
                
                # Handle video playback with precise timing
                if self.is_playing and self.video_cap:
                    # Initialize timing on first play frame
                    if video_start_time is None:
                        video_start_time = current_time
                        if self.audio_object and audio_start_time is None:
                            audio_start_time = current_time
                    
                    # Calculate current video time
                    video_elapsed = current_time - video_start_time
                    target_frame = int(video_elapsed * self.video_fps)
                    
                    # Set video position to target frame
                    self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                    video_success, video_frame = self.video_cap.read()
                    
                    if video_success:
                        video_frame = self._resize_frame(video_frame, self.video_width, self.video_height)
                    else:
                        # Video ended, loop back to start
                        self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        video_start_time = current_time  # Reset timing for loop
                        if self.audio_object:
                            audio_start_time = current_time
                        video_success, video_frame = self.video_cap.read()
                        if video_success:
                            video_frame = self._resize_frame(video_frame, self.video_width, self.video_height)
                else:
                    # Show first frame when not playing
                    if self.video_cap:
                        self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        video_success, video_frame = self.video_cap.read()
                        if video_success:
                            video_frame = self._resize_frame(video_frame, self.video_width, self.video_height)
                        else:
                            video_frame = np.zeros((self.video_height, self.video_width, 3), dtype=np.uint8)
                    else:
                        video_frame = np.zeros((self.video_height, self.video_width, 3), dtype=np.uint8)
                
                # Add countdown overlay if active
                if self.countdown_active:
                    webcam_frame = self._draw_countdown(webcam_frame, self.countdown_value)
                    video_frame = self._draw_countdown(video_frame, self.countdown_value)
                
                # Create side-by-side display
                combined_frame = np.hstack([video_frame, webcam_frame])
                
                # Add labels
                cv2.putText(combined_frame, "Reference Video", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(combined_frame, "Live Feed", (self.video_width + 10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # Add status text
                status_text = "Press 's' to start" if not self.is_playing and not self.countdown_active else ""
                if self.countdown_active:
                    status_text = f"Starting in {self.countdown_value}..."
                elif self.is_playing:
                    status_text = "Playing - Press 'r' to reset"
                
                if status_text:
                    text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                    text_x = (self.display_width - text_size[0]) // 2
                    cv2.putText(combined_frame, status_text, (text_x, self.video_height - 20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Display the combined frame
                cv2.imshow('Synchronized Dance Test', combined_frame)
                
                # Performance tracking
                frame_time = time.time() - self.last_frame_time
                self.frame_times.append(frame_time)
                if len(self.frame_times) > 30:  # Keep last 30 frames
                    self.frame_times.pop(0)
                self.last_frame_time = time.time()
                
                # Print performance info occasionally
                if len(self.frame_times) == 30:
                    avg_fps = 1.0 / np.mean(self.frame_times)
                    print(f"Average FPS: {avg_fps:.1f}")
        
        except Exception as e:
            print(f"Error in main loop: {e}")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        self.is_running = False
        self.is_playing = False
        self.countdown_active = False
        
        if self.video_cap:
            self.video_cap.release()
        if self.webcam_cap:
            self.webcam_cap.release()
        
        cv2.destroyAllWindows()
        
        # Stop audio
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=1.0)
        
        # Clean up temporary audio file
        if self.extracted_audio_path and os.path.exists(self.extracted_audio_path):
            try:
                os.remove(self.extracted_audio_path)
                print(f"Cleaned up temporary audio file: {self.extracted_audio_path}")
            except Exception as e:
                print(f"Could not remove temporary audio file: {e}")
        
        print("Cleanup complete")


# Example usage
if __name__ == "__main__":
    # Example usage - adjust paths as needed
    reference_video = "../data/reference_videos/magnetic.mp4"
    reference_audio = None  # Use audio from video, or specify separate audio file
    
    if not os.path.exists(reference_video):
        print(f"Reference video not found: {reference_video}")
        print("Please ensure the video file exists in the correct location.")
        sys.exit(1)
    
    try:
        interface = SyncTestInterface(reference_video, reference_audio)
        interface.run()
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
