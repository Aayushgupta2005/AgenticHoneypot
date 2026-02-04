
import requests
import time
import uuid

BASE_URL = "http://localhost:8003"
SESSION_ID = f"test-session-{uuid.uuid4()}"

def send_msg(text):
    payload = {
        "sessionId": SESSION_ID,
        "message": {
            "sender": "scammer",
            "text": text,
            "timestamp": int(time.time() * 1000)
        },
        "conversationHistory": []
    }
    try:
        # Using the key found in .env
        res = requests.post(f"{BASE_URL}/chat", json=payload, headers={"x-api-key": "abcdefghijkl"}) 
        # Config says: GUVI_API_KEY: str = os.getenv("GUVI_API_KEY") 
        # But wait, the route checks: if x_api_key != settings.GUVI_API_KEY:
        # So I need to set GUVI_API_KEY in .env or provide it.
        # I'll check .env content.
        print(f"Sent: {text}")
        if res.status_code == 200:
            print(f"Agent: {res.json().get('reply')}")
        else:
            print(f"Error {res.status_code}: {res.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    print(f"Starting simulation for session: {SESSION_ID}")
    
    # 1. Initial Scam Message
    send_msg("Your bank account is blocked. Click here to verify: http://phishing.com/verify")
    
    # 2. Follow up
    input("Press Enter for next turn...")
    send_msg("Why aren't you replying? Send me your UPI ID immediately.")
    
    # 3. Give Intel
    input("Press Enter for next turn...")
    send_msg("Okay, send money to scammer@okaxis")
