import cv2
import mediapipe as mp

# --- Setup ---
mp_tasks = mp.tasks
BaseOptions = mp_tasks.BaseOptions
VisionRunningMode = mp_tasks.vision.RunningMode

pose_model = "/Users/kadenwu/Downloads/pose_landmarker_full.task"
gesture_model = "/Users/kadenwu/Downloads/gesture_recognizer.task"

# Drawing utils
drawing_utils = mp.solutions.drawing_utils
drawing_styles = mp.solutions.drawing_styles

# --- Pose callback ---
def handle_pose_result(result, output_image, timestamp_ms):
    if not result.pose_landmarks:
        return

    annotated = output_image.numpy_view().copy()
    # Draw pose skeleton
    for landmarks in result.pose_landmarks:
        drawing_utils.draw_landmarks(
            image=annotated,
            landmark_list=landmarks,
            connections=mp.solutions.pose.POSE_CONNECTIONS,
            landmark_drawing_spec=drawing_styles.get_default_pose_landmarks_style()
        )

    cv2.imshow("Pose + Gesture Detection", annotated)
    cv2.waitKey(1)

# --- Gesture callback ---
def handle_gesture_result(result, output_image, timestamp_ms):
    if result.gestures:
        gesture = result.gestures[0][0].category_name
        print(f"[Gesture]: {gesture}")

# --- Options ---
pose_options = mp_tasks.vision.PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=pose_model),
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=handle_pose_result
)

gesture_options = mp_tasks.vision.GestureRecognizerOptions(
    base_options=BaseOptions(model_asset_path=gesture_model),
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=handle_gesture_result
)

# --- Main Loop ---
cap = cv2.VideoCapture(0)

with (
    mp_tasks.vision.PoseLandmarker.create_from_options(pose_options) as pose_landmarker,
    mp_tasks.vision.GestureRecognizer.create_from_options(gesture_options) as gesture_recognizer
):
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))

        # Async calls
        pose_landmarker.detect_async(mp_image, timestamp_ms)
        gesture_recognizer.recognize_async(mp_image, timestamp_ms)

cap.release()
cv2.destroyAllWindows()
