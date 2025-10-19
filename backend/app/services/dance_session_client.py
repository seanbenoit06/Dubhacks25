import requests
import base64
import json
import time
from PIL import Image
import io

class DanceSessionClient:
    def __init__(self, base_url="http://localhost:5002"):
        self.base_url = base_url
        self.session_id = None
    
    def start_session(self):
        """Start a new dance session"""
        try:
            response = requests.post(f"{self.base_url}/start_session")
            if response.status_code == 200:
                result = response.json()
                self.session_id = result['session_id']
                print(f"✅ Session started: {self.session_id}")
                return True
            else:
                print(f"❌ Error starting session: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False
    
    def load_reference_video(self, video_name):
        """Load a reference video for comparison"""
        try:
            response = requests.post(f"{self.base_url}/load_reference", json={"video_name": video_name})
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Reference video loaded: {result['message']}")
                return True
            else:
                print(f"❌ Error loading reference: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False
    
    def send_snapshot(self, image_path):
        """Send an image snapshot for processing with real-time feedback"""
        try:
            # Load and encode image
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Send to backend
            response = requests.post(
                f"{self.base_url}/process_snapshot",
                json={'image': image_data}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Display results
                print(f"📸 Snapshot processed:")
                print(f"   Timestamp: {result['timestamp']}")
                print(f"   Pose detected: {'Yes' if result['pose_landmarks'] else 'No'}")
                print(f"   Hand landmarks: {len(result['hand_landmarks'])} hands")
                
                if result['comparison_result']:
                    similarity = result['comparison_result'].get('combined_score', 0.0)
                    print(f"   Similarity score: {similarity:.3f}")
                
                if result['live_feedback']:
                    print(f"   🎯 Live feedback: {result['live_feedback']}")
                
                return result
            else:
                print(f"❌ Error: {response.status_code} - {response.json()}")
                return None
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None
    
    def get_session_status(self):
        """Get current session status"""
        try:
            response = requests.get(f"{self.base_url}/session_status")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error getting status: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None
    
    def end_session(self):
        """End the current session and get summary feedback"""
        try:
            response = requests.post(f"{self.base_url}/end_session")
            if response.status_code == 200:
                result = response.json()
                print(f"\n🎉 Session Summary:")
                print(f"   Session ID: {result['session_id']}")
                print(f"   Total poses: {result['total_poses']}")
                print(f"   Average similarity: {result['average_similarity']:.3f}")
                print(f"   Session feedback: {result['session_summary']}")
                
                if result['detailed_feedback']:
                    print(f"\n📊 Detailed Feedback History:")
                    for i, feedback in enumerate(result['detailed_feedback'][-5:]):  # Show last 5
                        print(f"   {i+1}. {feedback['feedback']} (Score: {feedback['similarity_score']:.3f})")
                
                return result
            else:
                print(f"❌ Error ending session: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None
    
    def health_check(self):
        """Check if the service is running"""
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Service is healthy")
                print(f"   Reference loaded: {result['reference_loaded']}")
                print(f"   Active session: {result['active_session']}")
                return True
            else:
                print(f"❌ Service unhealthy: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Service not reachable: {e}")
            return False

def simulate_dance_session():
    """Simulate a complete dance session workflow"""
    print("🕺 Dance Session Simulation")
    print("=" * 50)
    
    client = DanceSessionClient()
    
    # 1. Health check
    print("\n1. Health Check:")
    if not client.health_check():
        print("❌ Service is not running. Please start the backend service first.")
        return
    
    # 2. Load reference video
    print("\n2. Loading Reference Video:")
    if not client.load_reference_video("magnetic"):
        print("❌ Failed to load reference video")
        return
    
    # 3. Start session
    print("\n3. Starting Dance Session:")
    if not client.start_session():
        print("❌ Failed to start session")
        return
    
    # 4. Simulate sending snapshots (normally from frontend webcam)
    print("\n4. Simulating Dance Session:")
    print("   (In real usage, frontend would capture webcam frames every 0.5s)")
    
    # Simulate some snapshots with different similarity levels
    for i in range(5):
        print(f"\n   📸 Snapshot {i+1}:")
        # In real usage, this would be actual webcam frames
        # For demo, we'll just show the workflow
        print("   [Webcam frame would be captured and sent here]")
        print("   → Processing pose landmarks...")
        print("   → Comparing with reference...")
        print("   → Generating live feedback...")
        
        # Simulate session status check
        status = client.get_session_status()
        if status:
            print(f"   Session progress: {status['pose_count']} poses, {status['session_duration']:.1f}s")
        
        time.sleep(1)  # Simulate 0.5s intervals
    
    # 5. End session and get feedback
    print("\n5. Ending Session:")
    client.end_session()
    
    print("\n✅ Complete dance session workflow demonstrated!")
    
    print("\n📋 Frontend Integration Workflow:")
    print("   1. Start session: POST /start_session")
    print("   2. Load reference: POST /load_reference?video_name=magnetic")
    print("   3. Send snapshots every 0.5s: POST /process_snapshot")
    print("   4. Receive live feedback in response")
    print("   5. End session: POST /end_session")
    print("   6. Receive comprehensive session summary")

if __name__ == "__main__":
    simulate_dance_session()
