"""
Quick Server Test - Manual verification
"""

import requests
import socket


def test_connection():
    """Test berbagai cara koneksi"""

    urls_to_test = [
        "http://localhost:8000/health",
        "http://127.0.0.1:8000/health",
        "http://0.0.0.0:8000/health",
    ]

    print("🔍 Testing server connectivity...")

    for url in urls_to_test:
        try:
            print(f"\n📡 Testing: {url}")
            response = requests.get(url, timeout=5)
            print(f"✅ SUCCESS: HTTP {response.status_code}")
            print(f"📄 Response: {response.text[:100]}...")
            return True
        except Exception as e:
            print(f"❌ FAILED: {e}")

    # Test socket connection
    print(f"\n🔌 Testing socket connection to localhost:8000...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(("localhost", 8000))
        sock.close()

        if result == 0:
            print("✅ Socket connection successful - Server is listening!")
        else:
            print(f"❌ Socket connection failed - Error code: {result}")
    except Exception as e:
        print(f"❌ Socket test error: {e}")

    return False


if __name__ == "__main__":
    print("🚀 Quick Server Connectivity Test")
    print("=" * 40)

    if test_connection():
        print("\n🎉 Server is accessible!")
    else:
        print("\n⚠️ Server connection issues detected")
        print("\n💡 Try these solutions:")
        print("1. Start server in current terminal:")
        print("   python -m uvicorn api_server:app --host 0.0.0.0 --port 8000")
        print("2. Or check if server is still loading models...")
        print("3. Or try accessing http://localhost:8000/docs in browser")
