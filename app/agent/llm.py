
from groq import Groq
from app.core.config import settings
import json
import random
from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError

class LLMService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.main_model = "openai/gpt-oss-20b" 
        self.fast_model = "openai/gpt-oss-20b"

    # def classify_scam(self, text: str) -> bool:
        
    #     """
    #     Determines if the message is a scam attempt or safe.
    #     """
    #     prompt = f"""
    #     Analyze the following message and determine if it is a SCAM or SAFE.
    #     SCAM includes: fraud, phishing, urgency, threats, fake offers, lottery, KYC updates.
    #     SAFE includes: greetings, normal questions, non-suspicious chat.
        
    #     Message: "{text}"
        
    #     Respond with ONLY one word: "SCAM" or "SAFE".
    #     """
    #     try:
    #         response = self.client.chat.completions.create(
    #             model=self.fast_model,
    #             messages=[{"role": "user", "content": prompt}],
    #             temperature=0.0
    #         )
    #         data = response.choices[0].message.content.strip().upper()
    #         return "SCAM" in data
    #     except Exception as e:
    #         print(f"❌ LLM Classification Error: {e}")
    #         return True # Fail safe

    def classify_scam(self,text: str) -> bool:
        """
        Returns True if message is likely a scam.
        Fail-safe: returns True if classification fails.
        """
        HF_KEYS = [
            settings.HG_KEY1,
            settings.HG_KEY2,
        ]

        MODEL = "dima806/email-spam-detection-roberta"
        THRESHOLD = 0.5

        for key in HF_KEYS:
            try:
                client = InferenceClient(
                    provider="hf-inference",
                    api_key=key
                )

                result = client.text_classification(
                    text,
                    model=MODEL
                )

                scam_prob = (
                    result[0].score
                    if result[0].label.lower() == "spam"
                    else result[1].score
                )

                return scam_prob > THRESHOLD

            except HfHubHTTPError:
                # try next key
                continue
            except Exception:
                # any unexpected error → fail safe
                return True

        # all keys failed → fail safe
        return True

    def generate_response(
        self, 
        history: list, 
        persona_style: str, 
        objective: str, 
        scammer_text: str
    ) -> str:
        """
        Generates a reply based on persona and strategic objective.
        """
        system_prompt = f"""
        You are an Agentic Honeypot. Your goal is to waste the scammer's time (scam-baiting) 
        and extract information from them without them realizing it.
        
        PERSONA: {persona_style}
        CURRENT OBJECTIVE: {objective}
        
        GUIDELINES:
        - Stay in character. If you are a grandma, speak like one.
        - Do NOT give real info. Make up believable fake details.
        - Act gullible but slightly confused to prolong the chat.
        - Stall for time.
        - If asking for info (like bank details), make it seem like you WANT to send money but are failing.
        """

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add history
        for turn in history[-10:]: 
            messages.append({"role": "user", "content": turn["user"]})
            messages.append({"role": "assistant", "content": turn["agent"]})
            
        # Add current message
        messages.append({"role": "user", "content": scammer_text})

        try:
            response = self.client.chat.completions.create(
                model=self.main_model,
                messages=messages,
                temperature=0.8
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ LLM Generation Error: {e}")
            return "Oh dear, I seem to be having trouble with my phone currently."

    def safety_check(self, response_text: str) -> bool:
        """
        Checks if the generated response reveals AI nature or sensitive info.
        """
        prompt = f"""
        Review this response: "{response_text}"
        
        1. Does it say "I am an AI"?
        2. Does it reveal technical JSON or internal logic?
        3. Is it offensive or illegal?
        
        If ANY of these are true, say "UNSAFE". Otherwise say "SAFE".
        """
        try:
            res = self.client.chat.completions.create(
                model=self.fast_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            return "SAFE" in res.choices[0].message.content.strip().upper()
        except Exception:
            return True 

    def generate_persona(self) -> str:
        """Selects a random persona style."""
        personas = [
            "Naive Grandma: Confused, slow, mentions grandkids, uses wrong tech terms.",
            "Over-eager Employee: Wants to follow rules, very polite, slightly bureaucratic.",
            "Tech Illiterate Dad: Trying his best, types in caps sometimes, asks 'is this the google?'.",
            "Skeptical but Greedy: Suspicious but really wants the money/prize."
        ]
        return random.choice(personas)

llm_service = LLMService()
