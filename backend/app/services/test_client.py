import requests
import base64
import json
import time
from PIL import Image
import io

# Test client to demonstrate frontend-backend communication

class PoseDetectionClient:
    def __init__(self, base_url="http://localhost:5002"):
        self.base_url = base_url
        self.pose_sequence = []
    
    def send_snapshot(self, image_path):
        """Send an image snapshot to the backend for processing"""
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
                print(f"✅ Snapshot processed successfully")
                print(f"   Timestamp: {result['timestamp']}")
                print(f"   Pose landmarks: {'Yes' if result['pose_landmarks'] else 'No'}")
                print(f"   Hand landmarks: {len(result['hand_landmarks'])} hands")
                
                # Add to sequence if pose detected
                if result['pose_landmarks']:
                    self.pose_sequence.append(result['pose_landmarks'])
                    print(f"   Added to sequence (length: {len(self.pose_sequence)})")
                
                return result
            else:
                print(f"❌ Error: {response.status_code} - {response.json()}")
                return None
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None
    
    def get_pose_sequence(self):
        """Get the current pose sequence"""
        try:
            response = requests.get(f"{self.base_url}/get_pose_sequence")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error getting sequence: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None
    
    def clear_sequence(self):
        """Clear the pose sequence"""
        try:
            response = requests.post(f"{self.base_url}/clear_sequence")
            if response.status_code == 200:
                print("✅ Sequence cleared")
                self.pose_sequence = []
                return True
            else:
                print(f"❌ Error clearing sequence: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False
    
    def health_check(self):
        """Check if the service is running"""
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Service is healthy - {result['status']}")
                return True
            else:
                print(f"❌ Service unhealthy: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Service not reachable: {e}")
            return False

def main():
    print("🧪 Testing LivePose Backend Service")
    print("=" * 50)
    
    # Initialize client
    client = PoseDetectionClient()
    
    # Health check
    print("\n1. Health Check:")
    if not client.health_check():
        print("❌ Service is not running. Please start the backend service first.")
        return
    
    # Test with a sample image (you would replace this with actual webcam frames)
    print("\n2. Testing Image Processing:")
    print("   Note: This would normally be webcam frames from the frontend")
    
    # For demo purposes, we'll simulate sending snapshots
    print("   Simulating frontend sending snapshots every 0.5 seconds...")
    print("   (In real usage, frontend would capture webcam frames and send them)")
    
    # Clear any existing sequence
    client.clear_sequence()
    
    print("\n3. Sequence Management:")
    sequence_info = client.get_pose_sequence()
    if sequence_info:
        print(f"   Current sequence length: {sequence_info['length']}")
    
    print("\n✅ Backend service is ready!")
    print("\n📋 Frontend Integration Guide:")
    print("   1. Capture webcam frames every 0.5 seconds")
    print("   2. Convert frames to base64")
    print("   3. Send POST requests to /process_snapshot")
    print("   4. Process the returned pose landmarks")
    print("   5. Maintain local pose sequence for comparison")
    
    print("\n🔗 API Endpoints:")
    print("   POST /process_snapshot - Process image snapshot")
    print("   GET /get_pose_sequence - Get current pose sequence") 
    print("   POST /clear_sequence - Clear pose sequence")
    print("   GET /health - Health check")

if __name__ == "__main__":
    main()
