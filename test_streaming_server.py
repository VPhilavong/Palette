#!/usr/bin/env python3
"""
Test the streaming server functionality
"""

import sys
import requests
import time
import json
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get("http://localhost:8765/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_analyze_endpoint():
    """Test the analyze endpoint"""
    print("\n🔍 Testing analyze endpoint...")
    try:
        # Use current project as test
        data = {
            "projectPath": str(Path(__file__).parent)
        }
        
        response = requests.post(
            "http://localhost:8765/api/analyze",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Analyze endpoint passed")
            print(f"   Analysis: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Analyze endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Analyze endpoint error: {e}")
        return False

def test_generate_endpoint():
    """Test the generate endpoint (without streaming)"""
    print("\n🔍 Testing generate endpoint...")
    try:
        data = {
            "message": "create a simple button component",
            "projectPath": str(Path(__file__).parent),
            "conversationHistory": []
        }
        
        response = requests.post(
            "http://localhost:8765/api/generate",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Generate endpoint passed")
            print(f"   Response: {json.dumps(result, indent=2)}")
            
            # Try to connect to stream URL (just test the URL format)
            stream_url = result.get("streamUrl")
            if stream_url:
                print(f"   Stream URL: {stream_url}")
                return True
            else:
                print("❌ No stream URL in response")
                return False
        else:
            print(f"❌ Generate endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Generate endpoint error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Palette Streaming Server")
    print("=" * 50)
    
    tests = [
        test_health_check,
        test_analyze_endpoint,
        test_generate_endpoint
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The streaming server is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)