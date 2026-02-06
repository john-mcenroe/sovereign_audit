"""
Quick test script to verify the /analyze endpoint works
Run this to see detailed error output
"""
import requests
import json

url = "http://localhost:8000/analyze"
data = {"url": "https://example.com"}

print("=" * 80)
print("🧪 Testing /analyze endpoint")
print(f"📡 URL: {url}")
print(f"📦 Data: {json.dumps(data, indent=2)}")
print("=" * 80)

try:
    print("📤 Sending request...")
    response = requests.post(url, json=data, timeout=30)
    print(f"📥 Response status: {response.status_code}")
    print(f"📋 Response headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        print("✅ SUCCESS!")
        print(f"📊 Response: {json.dumps(response.json(), indent=2)}")
    else:
        print("❌ ERROR!")
        try:
            error_data = response.json()
            print(f"📄 Error response: {json.dumps(error_data, indent=2)}")
        except:
            print(f"📄 Error text: {response.text}")
            
except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}")
    import traceback
    traceback.print_exc()

print("=" * 80)
