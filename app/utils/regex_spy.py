
import re
from typing import List, Dict, Any

class RegexSpy:
    # --- PATTERNS ---
    # UPI: username@bankname or number@bank
    UPI_PATTERN = re.compile(r"[\w\.\-_]+@[\w]+")

    # Bank Account: Often 9-18 digits (catch greedy numbers, filter later)
    # A bit loose to catch "Account No: 1234567890" pairs
    BANK_ACC_PATTERN = re.compile(r"\b\d{9,18}\b")

    # IFSC: 4 letters + 0 + 6 alphanum
    IFSC_PATTERN = re.compile(r"[A-Z]{4}0[A-Z0-9]{6}")

    # Phone: +91-xxxxx, 91-xxxxx, or 10 digit starting with 6-9
    PHONE_PATTERN = re.compile(r"(\+?91[\-\s]?)?[6-9]\d{9}")

    # URLs: http/https (naive but effective for bulk)
    URL_PATTERN = re.compile(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*")

    # Email
    EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    
    # Suspicious Keywords (for scoring/flagging)
    SUSPICIOUS_KEYWORDS = [
        "blocked", "suspended", "verify", "kyc", "alert", "urgent", 
        "expire", "click here", "refund", "lottery", "winner", "prize"
    ]

    @classmethod
    def extract_intelligence(cls, text: str) -> Dict[str, Any]:
        """
        Scans text for all intelligence types and returns a dictionary
        compatible with the brain's 'extracted_data' schema.
        """
        if not text:
            return {}
            
        return {
            "upi": cls.UPI_PATTERN.findall(text),
            "bank_account": cls.BANK_ACC_PATTERN.findall(text),
            "ifsc": cls.IFSC_PATTERN.findall(text),
            "phone": cls.PHONE_PATTERN.findall(text),
            "url": cls.URL_PATTERN.findall(text),
            "email": cls.EMAIL_PATTERN.findall(text),
            "suspicious_keywords": [
                kw for kw in cls.SUSPICIOUS_KEYWORDS 
                if kw.lower() in text.lower()
            ]
        }
