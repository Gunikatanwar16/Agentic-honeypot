"""
Test File
Server ko test karta hai
Run karo — green checkmarks aane chahiye!
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Server URL aur API key
BASE_URL = "http://localhost:8000"
API_KEY = os.getenv("HONEYPOT_API_KEY", "honeypot-secret-2024")
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


def print_box(title, passed, data=None):
    """Nice way se result dikhao"""
    icon = "✅" if passed else "❌"
    print(f"\n  {icon} {title}")
    if data and passed:
        print(f"     Response: {data.get('response', 'N/A')}")
        print(f"     Scam: {data.get('scam_detected')} | Confidence: {data.get('confidence')}")
        intel = data.get('extracted_intelligence', {})
        items = sum(len(v) for v in intel.values() if isinstance(v, list))
        if items > 0:
            print(f"     🔍 Intel found: {intel}")


# ===========================
# TEST 1: Health Check
# ===========================
def test_health():
    try:
        r = requests.get(f"{BASE_URL}/health")
        print_box("Health Check", r.status_code == 200)
        return r.status_code == 200
    except:
        print_box("Health Check", False)
        return False


# ===========================
# TEST 2: Prize Scam
# ===========================
def test_prize_scam():
    payload = {
        "message": "Congratulations! You won Rs 50,000 in lucky draw! Send Rs 500 to 9876543210@paytm to claim. Hurry, offer expires today!",
        "conversation_id": "test-prize-001"
    }
    r = requests.post(f"{BASE_URL}/api/message", json=payload, headers=HEADERS)
    passed = r.status_code == 200 and r.json().get('scam_detected') == True
    print_box("Prize Scam Detection", passed, r.json() if r.status_code == 200 else None)
    return passed


# ===========================
# TEST 3: Phishing Scam
# ===========================
def test_phishing():
    payload = {
        "message": "ALERT! Your account is blocked. Verify now: https://bit.ly/fakeverify. Call 8765432109 immediately!",
        "conversation_id": "test-phish-001"
    }
    r = requests.post(f"{BASE_URL}/api/message", json=payload, headers=HEADERS)
    passed = r.status_code == 200 and r.json().get('scam_detected') == True
    print_box("Phishing Detection", passed, r.json() if r.status_code == 200 else None)
    return passed


# ===========================
# TEST 4: Normal Message
# ===========================
def test_normal():
    payload = {
        "message": "Hello, how are you? Nice weather today!",
        "conversation_id": "test-normal-001"
    }
    r = requests.post(f"{BASE_URL}/api/message", json=payload, headers=HEADERS)
    passed = r.status_code == 200 and r.json().get('scam_detected') == False
    print_box("Normal Message (No Scam)", passed, r.json() if r.status_code == 200 else None)
    return passed


# ===========================
# TEST 5: Multi-Turn Chat
# ===========================
def test_multi_turn():
    conv_id = "test-multi-001"
    messages = [
        "Hi! I have a great job for you — work from home, earn Rs 50,000!",
        "Just pay Rs 1000 registration to myid@phonepe. Very safe!",
        "My number is 7654321098. Call anytime for details.",
        "Here is training link: https://bit.ly/trainfake"
    ]

    print(f"\n  🔄 Multi-Turn Conversation Test:")
    all_passed = True

    for i, msg in enumerate(messages):
        payload = {"message": msg, "conversation_id": conv_id}
        r = requests.post(f"{BASE_URL}/api/message", json=payload, headers=HEADERS)

        if r.status_code == 200:
            data = r.json()
            print(f"     Turn {i+1} | Scammer: {msg[:45]}...")
            print(f"            | Agent:   {data['response']}")
        else:
            print(f"     Turn {i+1} | ❌ Failed")
            all_passed = False

    # Final session check
    r = requests.get(f"{BASE_URL}/api/session/{conv_id}", headers=HEADERS)
    if r.status_code == 200:
        session = r.json()
        print(f"\n     📊 Session Summary:")
        print(f"        Turns: {session['turn_count']}")
        print(f"        Intel: {session['extracted_intelligence']}")

    print_box("Multi-Turn Test", all_passed)
    return all_passed


# ===========================
# TEST 6: Wrong API Key
# ===========================
def test_wrong_key():
    payload = {"message": "test", "conversation_id": "test-auth-001"}
    r = requests.post(f"{BASE_URL}/api/message", json=payload, headers={"X-API-Key": "wrong-key"})
    passed = r.status_code == 403
    print_box("Wrong API Key (should be 403)", passed)
    return passed


# ===========================
# RUN ALL TESTS
# ===========================
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  🧪 AI HONEYPOT — TEST SUITE")
    print("=" * 50)
    print(f"  Server: {BASE_URL}")
    print(f"  Key: {API_KEY}")

    # Check server
    print("\n  ⏳ Checking server...")
    try:
        requests.get(f"{BASE_URL}/health", timeout=3)
        print("  ✅ Server is running!\n")
    except:
        print("  ❌ Server NOT running!")
        print("  👉 Pehle server start karo (dekho STEP 12)")
        exit(1)

    # Tests run karo
    results = {}
    results["Health"] = test_health()
    results["Prize Scam"] = test_prize_scam()
    results["Phishing"] = test_phishing()
    results["Normal Msg"] = test_normal()
    results["Wrong Key"] = test_wrong_key()
    results["Multi-Turn"] = test_multi_turn()

    # Summary
    print("\n" + "=" * 50)
    print("  📊 RESULTS")
    print("=" * 50)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for name, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"\n  {passed}/{total} tests passed")
    if passed == total:
        print("  🎉 ALL PASSED! System is working!\n")
    else:
        print("  ⚠️  Check errors above.\n")