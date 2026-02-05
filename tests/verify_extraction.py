import sys
import os
import asyncio
import re

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agent.llm import llm_service
from app.utils.regex_spy import RegexSpy

def test_regex():
    print("\n--- Testing Regex ---")
    text = "Your KYC is pending. Please send UPI: ram123@okhdfc, addhar_number is - 123445, immediately. Call +919876543210"
    extracted = RegexSpy.extract_intelligence(text)
    print(f"Extracted: {extracted}")
    
    assert "ram123@okhdfc" in extracted.get("upi", []), "UPI not found"
    
    # Test phone specifically for capturing group bug
    phones = extracted.get("phone", [])
    print(f"Phones found: {phones}")
    # We expect full numbers, not empty strings or fragments
    for p in phones:
        assert len(p) >= 10, f"Phone number too short/fragmented: {p}"
        
    print("✅ Regex test passed")

def test_llm_extraction():
    print("\n--- Testing LLM Extraction (Direct) ---")
    text = "My crypto wallet is 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa and my OTP is 123456. "
    known_keys = list(RegexSpy.REGEX_PATTERNS.keys())
    known_keys_str = ",".join(known_keys)
    
    # This will make a real API call
    extracted = llm_service.extract_unknown_entities(text, known_keys_str)
    print(f"Extracted: {extracted}")
    
    # Check if crypto wallet or otp is found
    # Note: keys are lowercased and spaces replaced by underscores in our logic
    found = False
    for k, v in extracted.items():
        if "wallet" in k or "crypto" in k or "otp" in k:
            found = True
            break
            
    if found:
        print("✅ LLM Extraction test passed")
    else:
        print("⚠️ LLM Extraction might have failed or found nothing (check output)")
        
def test_regex_class_structure():
    # Verify the structure matches what Brain expects
    print("\n--- Testing Regex Class Structure ---")
    assert hasattr(RegexSpy, 'REGEX_PATTERNS'), "REGEX_PATTERNS missing"
    assert hasattr(RegexSpy, 'extract_intelligence'), "extract_intelligence missing"
    print("✅ Structure test passed")

if __name__ == "__main__":
    test_regex()
    test_regex_class_structure()
    test_llm_extraction()
