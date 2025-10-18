import cv2
import mediapipe as mp

# Initialize MediaPipe Pose, Hands, and Drawing
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Keep gesture model variable for future use
gesture_model = "/Users/kadenwu/Downloads/gesture_recognizer.task"

# Open webcam (0 = default camera)
cap = cv2.VideoCapture(0)

with mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,        # 0=Lite, 1=Full, 2=Heavy (slower, more accurate)
    enable_segmentation=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
) as pose, mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
) as hands:

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # Convert BGR (OpenCV) -> RGB (MediaPipe)
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process frame for pose landmarks
        pose_results = pose.process(image_rgb)
        
        # Process frame for hand landmarks (gestures)
        hand_results = hands.process(image_rgb)

        # Draw the pose on the frame (excluding hand landmarks to avoid redundancy)
        if pose_results.pose_landmarks:
            # Create a custom connections list without hand connections
            pose_connections = []
            for connection in mp_pose.POSE_CONNECTIONS:
                # Skip connections involving wrist landmarks (15, 16) and hand landmarks (17, 18, 19, 20)
                if not (connection[0] >= 15 and connection[0] <= 20) and not (connection[1] >= 15 and connection[1] <= 20):
                    pose_connections.append(connection)
            
            mp_drawing.draw_landmarks(
                frame,
                pose_results.pose_landmarks,
                pose_connections,
                mp_drawing.DrawingSpec(color=(0,255,0), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(255,0,0), thickness=2, circle_radius=2)
            )

        # Draw hand landmarks and connections
        if hand_results.multi_hand_landmarks and pose_results.pose_landmarks:
            for idx, hand_landmarks in enumerate(hand_results.multi_hand_landmarks):
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0,0,255), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(255,255,0), thickness=2, circle_radius=2)
                )
                
                # Connect hand wrist to corresponding elbow
                hand_wrist = hand_landmarks.landmark[0]  # Wrist landmark
                h, w, _ = frame.shape
                
                # Get image dimensions for coordinate conversion
                wrist_x = int(hand_wrist.x * w)
                wrist_y = int(hand_wrist.y * h)
                
                # Find the closest pose wrist landmark to connect to
                if pose_results.pose_landmarks:
                    # Get pose wrist landmarks (left wrist = 15, right wrist = 16)
                    left_pose_wrist = pose_results.pose_landmarks.landmark[15]
                    right_pose_wrist = pose_results.pose_landmarks.landmark[16]
                    
                    # Calculate distances to both pose wrists
                    left_wrist_x = int(left_pose_wrist.x * w)
                    left_wrist_y = int(left_pose_wrist.y * h)
                    right_wrist_x = int(right_pose_wrist.x * w)
                    right_wrist_y = int(right_pose_wrist.y * h)
                    
                    dist_to_left = ((wrist_x - left_wrist_x) ** 2 + (wrist_y - left_wrist_y) ** 2) ** 0.5
                    dist_to_right = ((wrist_x - right_wrist_x) ** 2 + (wrist_y - right_wrist_y) ** 2) ** 0.5
                    
                    # Connect to the closest pose wrist and its corresponding elbow
                    if dist_to_left < dist_to_right and left_pose_wrist.visibility > 0.5:
                        # Connect to left elbow (landmark 13)
                        if pose_results.pose_landmarks.landmark[13].visibility > 0.5:
                            elbow_x = int(pose_results.pose_landmarks.landmark[13].x * w)
                            elbow_y = int(pose_results.pose_landmarks.landmark[13].y * h)
                            cv2.line(frame, (wrist_x, wrist_y), (elbow_x, elbow_y), (255, 0, 255), 2)
                    elif right_pose_wrist.visibility > 0.5:
                        # Connect to right elbow (landmark 14)
                        if pose_results.pose_landmarks.landmark[14].visibility > 0.5:
                            elbow_x = int(pose_results.pose_landmarks.landmark[14].x * w)
                            elbow_y = int(pose_results.pose_landmarks.landmark[14].y * h)
                            cv2.line(frame, (wrist_x, wrist_y), (elbow_x, elbow_y), (255, 0, 255), 2)

        # Display gesture information
        if hand_results.multi_handedness:
            for idx, handedness in enumerate(hand_results.multi_handedness):
                label = handedness.classification[0].label
                confidence = handedness.classification[0].score
                cv2.putText(frame, f"{label} Hand: {confidence:.2f}", 
                           (10, 30 + idx * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Flip horizontally for a mirror-like effect
        frame = cv2.flip(frame, 1)
        cv2.imshow('Live Pose + Gesture Detection', frame)

        # Exit with ESC key
        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
