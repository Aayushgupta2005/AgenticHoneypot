
import re
from typing import List, Dict, Any

class RegexSpy:
    # --- PATTERNS ---
    REGEX_PATTERNS = {
        "upi": [
            r"(?i)\b[a-z0-9][a-z0-9._-]{1,254}@[a-z0-9]{2,64}\b(?!\.)"
        ],
        "email": [
            r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}\b"
        ],
        # Phone: +91-xxxxx, 91-xxxxx, or 10 digit starting with 6-9
        "phone": [
            r"(?:\+?91[\-\s]?)?[6-9]\d{9}\b"
        ],
        "url": [
            r"https?://\S+",
            r"www.\S+"
        ],
        "bank_account": [
            r"\b\d{9,18}\b"
        ],
        "ifsc": [
            r"\b[A-Z]{4}0[A-Z0-9]{6}\b"
        ]
    }

    EXTRACTION_ORDER = [
        "url",
        "email",
        "upi",
        "phone",
        "ifsc",
        "bank_account"
    ]
    
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
        extracted = {}
        working_text = text

        for field in cls.EXTRACTION_ORDER:
            for pattern in cls.REGEX_PATTERNS.get(field, []):
                matches = re.findall(pattern, working_text, flags=re.IGNORECASE)

                if not matches:
                    continue

                cleaned = set()
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    cleaned.add(match)
                    # Remove from text to avoid overlapping matches (e.g. phone in url)
                    working_text = working_text.replace(match, " ")

                if cleaned:
                    extracted[field] = list(cleaned)

        # Add suspicious keywords check separately as it's not a regex extraction in the same way
        suspicious = [
            kw for kw in cls.SUSPICIOUS_KEYWORDS 
            if kw.lower() in text.lower()
        ]
        if suspicious:
            extracted["suspicious_keywords"] = suspicious

        return extracted
        }
