import sys
import os
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

from app.agent.llm import llm_service

def test_scam_detection():
    output = []
    output.append("--- Testing Scam Classification ---")
    
    # Check Env
    import os
    k1 = os.getenv("HG_KEY1")
    k2 = os.getenv("HG_KEY2")
    output.append(f"HG_KEY1 present: {bool(k1)}")
    output.append(f"HG_KEY2 present: {bool(k2)}")

    # Test 1: Obvious Scam
    scam_text = "Urgent: Your account is blocked. Verify KYC immediately by clicking here: http://bit.ly/scam"
    output.append(f"Testing Scam Text: '{scam_text}'")
    try:
        is_scam = llm_service.classify_scam(scam_text)
        output.append(f"Result: {'SCAM' if is_scam else 'SAFE'}")
        
        if is_scam:
             output.append("✅ Scam detected correctly.")
        else:
             output.append("❌ Failed to detect scam.")
    except Exception as e:
        output.append(f"❌ Error during call: {e}")

    # Test 2: Safe Text
    safe_text = "Hi grandma, how are you doing today? I missed your call."
    output.append(f"\nTesting Safe Text: '{safe_text}'")
    try:
        is_scam = llm_service.classify_scam(safe_text)
        output.append(f"Result: {'SCAM' if is_scam else 'SAFE'}")
        
        if not is_scam:
             output.append("✅ Safe text passed correctly.")
        else:
             output.append("❌ Safe text flagged as scam.")
    except Exception as e:
        output.append(f"❌ Error during call: {e}")

    with open("scam_test_result.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))
    
    print("Test completed. See scam_test_result.txt")

if __name__ == "__main__":
    test_scam_detection()
