import cv2
import mediapipe as mp
import numpy as np
import time
import base64
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from io import BytesIO
from PIL import Image
from pose_comparison_service import PoseComparisonService
from pose_comparison_config import PoseComparisonConfig, DEFAULT_CONFIG, DANCE_CONFIG
from angle_calculator import AngleCalculator
from typing import Optional, List, Dict, Any
import json

# Initialize MediaPipe pose and hands
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

app = FastAPI(title="LivePose Backend Service", description="Process image snapshots for pose detection")

# Pydantic models for request/response
class ImageSnapshotRequest(BaseModel):
    image: str  # base64 encoded image

class ProcessSnapshotResponse(BaseModel):
    timestamp: float
    pose_landmarks: Optional[List[List[float]]] = None
    hand_landmarks: List[List[List[float]]] = []
    hand_classifications: List[Dict[str, Any]] = []
    preprocessed_angles: Dict[str, float] = {}
    comparison_result: Optional[Dict[str, Any]] = None
    live_feedback: Optional[str] = None
    success: bool
    error: Optional[str] = None

class SessionFeedbackRequest(BaseModel):
    session_id: str
    include_summary: bool = True

class SessionFeedbackResponse(BaseModel):
    session_id: str
    total_poses: int
    average_similarity: float
    session_summary: str
    detailed_feedback: list = []

class LoadReferenceRequest(BaseModel):
    video_name: str

class UpdateConfigRequest(BaseModel):
    pose_weight: Optional[float] = None
    motion_weight: Optional[float] = None
    dtw_enabled: Optional[bool] = None
    preset: Optional[str] = None  # "default", "dance", "position_focused", "motion_focused"

# Initialize pose detection
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    enable_segmentation=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Initialize hand detection
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Store pose sequence for comparison
pose_sequence = []
MAX_SEQUENCE_LENGTH = 100  # Keep last 100 poses (50 seconds at 0.5s intervals)

# Session management
current_session = {
    'session_id': None,
    'start_time': None,
    'pose_data': [],
    'feedback_history': [],
    'reference_video': None
}

# Pose comparison service
comparison_service = None

# Global configuration
current_config = DEFAULT_CONFIG
angle_calculator = AngleCalculator()

def load_reference_video(video_name):
    """Load reference video for comparison"""
    global comparison_service
    try:
        # Get the correct path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_dir, "..", "data", "processed_poses", f"{video_name}_poses.npy")

        # Load the numpy array (list of pose data)
        reference_data = np.load(data_path, allow_pickle=True)
        
        # Convert to the format expected by PoseComparisonService
        # Filter frames with poses and convert to the expected format
        reference_poses_list = []
        for frame_data in reference_data:
            if frame_data.get('has_pose', False):
                # Create the format expected by PoseComparisonService
                pose_dict = {
                    'landmarks': frame_data['landmarks'],
                    'timestamp': frame_data['timestamp'],
                    'frame_number': frame_data['frame_number']
                }
                reference_poses_list.append(pose_dict)
        
        comparison_service = PoseComparisonService(reference_poses_list, current_config)
        current_session['reference_video'] = video_name
        print(f"Loaded {len(reference_poses_list)} reference poses from {video_name}")
        return True
    except Exception as e:
        print(f"Error loading reference video: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_live_feedback(comparison_result):
    """Generate live feedback based on pose comparison"""
    if not comparison_result:
        return "No pose detected"
    
    similarity_score = comparison_result.get('combined_score', 0.0)
    
    if similarity_score >= 0.8:
        return "Excellent! Great form!"
    elif similarity_score >= 0.6:
        return "Good job! Keep it up!"
    elif similarity_score >= 0.4:
        return "Getting there! Try to match the reference more closely."
    elif similarity_score >= 0.2:
        return "Room for improvement. Focus on the key poses."
    else:
        return "Let's work on the basics. Try to follow the reference more closely."

def generate_llm_feedback(user_pose_data, comparison_results, reference_pose_data=None):
    """Generate LLM feedback based on pose data and comparison results"""
    # Check if we need detailed feedback based on score threshold
    combined_score = comparison_results.get('combined_score', 0.0)
    
    if combined_score >= current_config.min_score_threshold:
        return f"Great pose! Your similarity score is {combined_score:.1%}. Keep it up!"
    
    # Only provide detailed feedback if score is below threshold
    feedback_parts = []
    
    # Add score information
    feedback_parts.append(f"Current similarity: {combined_score:.1%} (pose: {comparison_results.get('pose_score', 0):.1%}, motion: {comparison_results.get('motion_score', 0):.1%})")
    
    # Add angle differences if reference data is available
    if reference_pose_data and 'angles' in reference_pose_data:
        user_angles = user_pose_data.get('angles', {})
        ref_angles = reference_pose_data.get('angles', {})
        
        angle_feedback = []
        for angle_name, user_angle in user_angles.items():
            if angle_name in ref_angles:
                ref_angle = ref_angles[angle_name]
                difference = abs(user_angle - ref_angle)
                
                if difference > current_config.angle_difference_threshold:
                    if user_angle > ref_angle:
                        angle_feedback.append(f"{angle_name.replace('_', ' ').title()}: bend less by {difference:.1f}°")
                    else:
                        angle_feedback.append(f"{angle_name.replace('_', ' ').title()}: bend more by {difference:.1f}°")
        
        if angle_feedback:
            feedback_parts.append("Angle adjustments needed: " + ", ".join(angle_feedback))
    
    # Add position differences if reference data is available
    if reference_pose_data and 'landmarks' in reference_pose_data:
        user_landmarks = user_pose_data.get('landmarks', {})
        ref_landmarks = reference_pose_data.get('landmarks', {})
        
        position_feedback = []
        for category, landmarks in user_landmarks.items():
            if category in ref_landmarks:
                for landmark_name, user_pos in landmarks.items():
                    if landmark_name in ref_landmarks[category]:
                        ref_pos = ref_landmarks[category][landmark_name]
                        if user_pos is not None and ref_pos is not None:
                            # Calculate 3D distance
                            distance = np.linalg.norm(np.array(user_pos) - np.array(ref_pos))
                            
                            if distance > current_config.position_difference_threshold:
                                position_feedback.append(f"{landmark_name.replace('_', ' ').title()}: adjust position")
        
        if position_feedback:
            feedback_parts.append("Position adjustments needed: " + ", ".join(position_feedback[:3]))  # Limit to 3 items
    
    # Combine feedback
    if len(feedback_parts) > 1:
        return " | ".join(feedback_parts)
    else:
        return feedback_parts[0] if feedback_parts else "Keep practicing to improve your pose!"

def process_image_snapshot(image_data):
    """Process a single image snapshot and extract pose/hand landmarks"""
    try:
        # Convert base64 to image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process pose
        pose_results = pose.process(rgb_frame)
        
        # Process hands
        hand_results = hands.process(rgb_frame)
        
        # Extract landmarks
        pose_landmarks = None
        hand_landmarks = []
        hand_classifications = []
        preprocessed_angles = {}
        
        if pose_results.pose_landmarks:
            # Convert pose landmarks to numpy array
            pose_landmarks = np.array([[lm.x, lm.y, lm.z, lm.visibility] for lm in pose_results.pose_landmarks.landmark])
        
        if hand_results.multi_hand_landmarks:
            for idx, hand_landmark in enumerate(hand_results.multi_hand_landmarks):
                # Convert hand landmarks to numpy array
                hand_array = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmark.landmark])
                hand_landmarks.append(hand_array)
                
                # Get hand classification
                if hand_results.multi_handedness and idx < len(hand_results.multi_handedness):
                    handedness = hand_results.multi_handedness[idx]
                    hand_classifications.append({
                        'label': handedness.classification[0].label,
                        'confidence': handedness.classification[0].score
                    })
        
        # Calculate preprocessed angles if we have pose landmarks
        if pose_landmarks is not None:
            try:
                # Flatten pose landmarks for angle calculation (x, y, z coordinates only)
                pose_flat = pose_landmarks[:, :3].flatten()
                
                # Calculate angles for each hand if available
                hand_angles = []
                if hand_landmarks:
                    for hand_landmark in hand_landmarks:
                        hand_flat = hand_landmark.flatten()
                        hand_angles.append(hand_flat)
                
                # Calculate all angles
                if hand_angles:
                    # Use first hand for angle calculation
                    preprocessed_angles = angle_calculator.calculate_all_angles(pose_flat, hand_angles[0])
                else:
                    preprocessed_angles = angle_calculator.calculate_all_angles(pose_flat)
                    
            except Exception as e:
                print(f"Error calculating angles: {e}")
                preprocessed_angles = {}
        
        # Perform real-time comparison if service is available
        comparison_result = None
        live_feedback = None
        
        if pose_landmarks is not None and comparison_service is not None:
            try:
                # Compare with reference
                comparison_result = comparison_service.update_user_pose(pose_landmarks)
                
                # Get reference pose data for detailed feedback
                reference_pose_data = None
                if comparison_result and 'best_match_idx' in comparison_result:
                    best_match_idx = comparison_result['best_match_idx']
                    if best_match_idx < len(comparison_service.reference_poses):
                        ref_pose = comparison_service.reference_poses[best_match_idx]
                        
                        # Calculate reference angles and landmarks
                        ref_landmarks_flat = ref_pose['landmarks'][:, :3].flatten()
                        ref_angles = angle_calculator.calculate_all_angles(ref_landmarks_flat)
                        ref_key_landmarks = angle_calculator.extract_key_landmarks(ref_landmarks_flat)
                        
                        reference_pose_data = {
                            'angles': ref_angles,
                            'landmarks': ref_key_landmarks
                        }
                
                # Generate detailed feedback with reference data
                user_pose_data = {
                    'angles': preprocessed_angles,
                    'landmarks': angle_calculator.extract_key_landmarks(pose_flat) if pose_landmarks is not None else {}
                }
                
                live_feedback = generate_llm_feedback(user_pose_data, comparison_result, reference_pose_data)
                
                # Store in session data
                current_session['pose_data'].append({
                    'timestamp': time.time(),
                    'pose_landmarks': pose_landmarks,
                    'comparison_result': comparison_result
                })
                current_session['feedback_history'].append({
                    'timestamp': time.time(),
                    'feedback': live_feedback,
                    'similarity_score': comparison_result.get('combined_score', 0.0)
                })
                
            except Exception as e:
                print(f"Error in pose comparison: {e}")
                comparison_result = None
                live_feedback = "Comparison unavailable"
        
        # Create result
        result = {
            'timestamp': time.time(),
            'pose_landmarks': pose_landmarks.tolist() if pose_landmarks is not None else None,
            'hand_landmarks': [hand.tolist() for hand in hand_landmarks],
            'hand_classifications': hand_classifications,
            'preprocessed_angles': preprocessed_angles,
            'comparison_result': comparison_result,
            'live_feedback': live_feedback,
            'success': True
        }
        
        # Add to sequence for comparison
        if pose_landmarks is not None:
            pose_sequence.append(pose_landmarks)
            if len(pose_sequence) > MAX_SEQUENCE_LENGTH:
                pose_sequence.pop(0)
        
        return result
        
    except Exception as e:
        return {
            'timestamp': time.time(),
            'pose_landmarks': None,
            'hand_landmarks': [],
            'hand_classifications': [],
            'preprocessed_angles': {},
            'success': False,
            'error': str(e)
        }

@app.post('/process_snapshot', response_model=ProcessSnapshotResponse)
async def process_snapshot(request: ImageSnapshotRequest):
    """Endpoint to process image snapshots from frontend"""
    try:
        if not request.image:
            raise HTTPException(status_code=400, detail='No image data provided')
        
        result = process_image_snapshot(request.image)
        return ProcessSnapshotResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/get_pose_sequence')
async def get_pose_sequence():
    """Get the current pose sequence for comparison"""
    return {
        'sequence': [pose.tolist() for pose in pose_sequence],
        'length': len(pose_sequence)
    }

@app.post('/clear_sequence')
async def clear_sequence():
    """Clear the pose sequence"""
    global pose_sequence
    pose_sequence = []
    return {'success': True, 'message': 'Sequence cleared'}

@app.post('/start_session')
async def start_session():
    """Start a new dance session"""
    global current_session
    session_id = f"session_{int(time.time())}"
    current_session = {
        'session_id': session_id,
        'start_time': time.time(),
        'pose_data': [],
        'feedback_history': [],
        'reference_video': current_session.get('reference_video')
    }
    return {'session_id': session_id, 'message': 'Session started successfully'}

@app.post('/end_session', response_model=SessionFeedbackResponse)
async def end_session():
    """End current session and get summary feedback"""
    global current_session
    
    if not current_session['session_id']:
        raise HTTPException(status_code=400, detail='No active session to end')
    
    # Generate session summary
    total_poses = len(current_session['pose_data'])
    if total_poses > 0:
        similarity_scores = [data['comparison_result'].get('combined_score', 0.0) 
                           for data in current_session['pose_data'] 
                           if data['comparison_result']]
        average_similarity = np.mean(similarity_scores) if similarity_scores else 0.0
    else:
        average_similarity = 0.0
    
    # Generate LLM feedback
    comparison_results = [data['comparison_result'] for data in current_session['pose_data'] 
                         if data['comparison_result']]
    session_summary = generate_llm_feedback(current_session['pose_data'], comparison_results)
    
    response = SessionFeedbackResponse(
        session_id=current_session['session_id'],
        total_poses=total_poses,
        average_similarity=float(average_similarity),
        session_summary=session_summary,
        detailed_feedback=current_session['feedback_history']
    )
    
    # Reset session (but keep reference video loaded)
    reference_video = current_session.get('reference_video')
    current_session = {
        'session_id': None,
        'start_time': None,
        'pose_data': [],
        'feedback_history': [],
        'reference_video': reference_video
    }
    
    return response

@app.post('/load_reference')
async def load_reference_video_endpoint(request: LoadReferenceRequest):
    """Load a reference video for comparison"""
    try:
        success = load_reference_video(request.video_name)
        if success:
            return {"message": f"Reference video {request.video_name} loaded successfully"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to load reference video {request.video_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/update_config')
async def update_config(request: UpdateConfigRequest):
    """Update pose comparison configuration"""
    global current_config, comparison_service
    
    try:
        # Handle preset configurations
        if request.preset:
            if request.preset == "default":
                new_config = DEFAULT_CONFIG
            elif request.preset == "dance":
                new_config = DANCE_CONFIG
            elif request.preset == "position_focused":
                new_config = PoseComparisonConfig(pose_weight=0.9, motion_weight=0.1)
            elif request.preset == "motion_focused":
                new_config = PoseComparisonConfig(pose_weight=0.3, motion_weight=0.7)
            else:
                raise HTTPException(status_code=400, detail=f"Unknown preset: {request.preset}")
        else:
            # Update individual parameters
            new_config = PoseComparisonConfig(
                pose_weight=request.pose_weight or current_config.pose_weight,
                motion_weight=request.motion_weight or current_config.motion_weight,
                dtw_enabled=request.dtw_enabled if request.dtw_enabled is not None else current_config.dtw_enabled,
                smoothing_window=current_config.smoothing_window,
                dtw_window=current_config.dtw_window,
                dtw_interval=current_config.dtw_interval
            )
        
        # Validate weights sum to 1.0
        if abs(new_config.pose_weight + new_config.motion_weight - 1.0) > 0.001:
            raise HTTPException(status_code=400, detail="Pose and motion weights must sum to 1.0")
        
        # Update global config
        current_config = new_config
        
        # Update comparison service if it exists
        if comparison_service:
            comparison_service.update_config(current_config)
        
        return {
            "message": "Configuration updated successfully",
            "config": current_config.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/get_config')
async def get_config():
    """Get current configuration"""
    return {"config": current_config.to_dict()}

@app.get('/session_status')
async def get_session_status():
    """Get current session status"""
    return {
        'session_id': current_session['session_id'],
        'start_time': current_session['start_time'],
        'pose_count': len(current_session['pose_data']),
        'reference_video': current_session['reference_video'],
        'session_duration': time.time() - current_session['start_time'] if current_session['start_time'] else 0
    }

@app.get('/health')
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy', 
        'timestamp': time.time(),
        'reference_loaded': comparison_service is not None,
        'active_session': current_session['session_id'] is not None
    }

if __name__ == "__main__":
    print("Starting LivePose backend service...")
    print("Available endpoints:")
    print("  POST /process_snapshot - Process image snapshot with real-time comparison")
    print("  POST /start_session - Start a new dance session")
    print("  POST /end_session - End session and get summary feedback")
    print("  POST /load_reference - Load reference video for comparison")
    print("  GET /session_status - Get current session status")
    print("  GET /get_pose_sequence - Get current pose sequence")
    print("  POST /clear_sequence - Clear pose sequence")
    print("  GET /health - Health check")
    print("  GET /docs - FastAPI documentation")
    
    import uvicorn
    uvicorn.run("livepose:app", host="0.0.0.0", port=5002, reload=True)