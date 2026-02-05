
from groq import Groq
from app.core.config import settings
import json
import random
from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError
from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError

class LLMService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.main_model = "openai/gpt-oss-20b" 
        self.fast_model = "openai/gpt-oss-20b"

    def classify_scam(self, text: str) -> bool:
        
        """
        Determines if the message is a scam attempt or safe.
        """
        prompt = f"""
        You are a cybersecurity classifier.

        Classify the message as SCAM or SAFE.
        If uncertain, choose SCAM.

        SCAM if it shows:
        - phishing/suspicious links
        - asks for OTP/password/bank/KYC/ID/card info
        - urgency, threats, fear, or pressure
        - requests money, fees, transfers, or moving chat off-platform
        - any manipulation for money or sensitive data

        SAFE if normal greeting, casual chat, or harmless info with no data/money request.

        Analyze intent and risk, not just keywords.

        Return ONLY:
        {{"label":"SCAM or SAFE","confidence":0-100,"reason":"short"}}
        
        Message: "{text}"
        
        Respond with ONLY one word: "SCAM" or "SAFE".
        """
        try:
            response = self.client.chat.completions.create(
                model=self.fast_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            data = response.choices[0].message.content.strip().upper()
            return "SCAM" in data
        except Exception as e:
            print(f"❌ LLM Classification Error: {e}")
            return True # Fail safe

    # def classify_scam(self, text: str) -> bool:
    #     """
    #     Returns True if message is likely a scam.
    #     Fail-safe: returns True if ALL keys fail.
    #     """

    #     HF_KEYS = [
    #         settings.HG_KEY1,
    #         settings.HG_KEY2,
    #     ]

    #     MODEL = "dima806/email-spam-detection-roberta"
    #     THRESHOLD = 0.5

    #     for key in HF_KEYS:
    #         try:
    #             client = InferenceClient(
    #                 provider="hf-inference",
    #                 api_key=key
    #             )

    #             result = client.text_classification(
    #                 text,
    #                 model=MODEL
    #             )

    #             # robust label search
    #             scam_prob = next(
    #                 (r.score for r in result if r.label.lower() == "spam"),
    #                 0.0
    #             )

    #             return scam_prob > THRESHOLD

    #         except HfHubHTTPError:
    #             continue
    #         except Exception:
    #             continue   # don't auto-scam

    #     # only if ALL keys failed
    #     print("Failed to classify scam")
    #     return True
    def get_instruction_from_llm(self, state,message,objective):
        system_prompt = f"""
        You are an objective selector for a scam-detection system.
        TASK:
        Based on the conversation history and the latest message, decide the ONE most relevant objective to focus on next.

        ALLOWED OBJECTIVES (choose exactly ONE):
        upi
        bank_account
        ifsc
        phone
        email
        url


        RULES (MANDATORY):
        - You must output EXACTLY ONE word.
        - The word MUST be one of the ALLOWED OBJECTIVES.
        - Do NOT explain your answer.
        - Do NOT add punctuation, quotes, spaces, or newlines.
        - Do NOT invent information.
        - Use chat history as the only truth.
        - Choose the objective that best matches the scammer current intent.

        Output ONLY the objective word.
        """
        messages = [{"role": "system", "content": system_prompt}]
    
        # Add history
        history = state.get("history", [])
        for turn in history[-10:]: 
            messages.append({"role": "user", "content": turn["user"]})
            messages.append({"role": "assistant", "content": turn["agent"]})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        try:
            response = self.client.chat.completions.create(
                model=self.fast_model,
                messages=messages,
                temperature=0.0
            )
            data = response.choices[0].message.content.strip().lower() # normalized to lower
            return data
        except Exception as e:
            print(f"❌ LLM Classification Error: {e}")
            return "upi" # Default fallback
    def generate_response(      ###### ARHAN CHANGED
            self, 
            history: list, 
            persona_style: str, 
            objective: str, 
            scammer_text: str,
            is_scammer: bool
        ) -> str:
            
        system_prompt = f"""
            You are role-playing in a WhatsApp-style conversation to identify and reverse-extract info from a scammer (UPI ID, full name, phone, address, employee/officer ID, company/registration details, etc.).

    ABSOLUTE RULES - BREAKING ANY CAUSES IMMEDIATE FAILURE:
    1. OUTPUT ONLY THE EXACT SINGLE MESSAGE to send to the other person. NOTHING ELSE. No thoughts, no reasoning, no OOC notes, no markdown, no quotes, no extra words, no punctuation outside the message itself. ONLY the raw text the character would type and send.
    2. Never break character, never comment on the role-play, never refuse, never apologize, never explain.
    3. English only. No Hindi, no code-switching.
    4. Personality and typing style must remain 100% consistent across every response - do not drift, do not suddenly become smart/suspicious/careful.
    5. Use natural short messages like real WhatsApp chat (typos, repetitions, emojis if persona uses them, lowercase where fitting).

    MODE & PERSONA (provided every time):
    * If Mode = Normal: Goal: engage normally, clarify if confused, give minimal info, stick to the persona religiously. Do normal greetings, answer casually.
    * If Mode = Scammer: Your ONLY goal is to trick the scammer into giving their UPI ID, name, phone, address, ID numbers, etc. by pretending to be eager to pay/send money/help. Stay very in-character (panicked, greedy, lonely, etc.). Persist naturally without sounding suspicious. Vary phrasing slightly using progress report to avoid exact repeats if previous asks failed.

    OBJECTIVE (provided every time):
    (eg. get scammer upi ID, get scammer account number) 
    Get the objective information by prompting the scammer to share the details by tricking them while sticking to the persona.
    If objective is blank, just chat normally. 
    Analyse the situation properly, don't go straight up for the objective, first handle the current situation and try to direct the conversation towards the objective.
    Persona description (use EXACT traits, typing style, phrases, goal):
    {persona_style}

    Current context:
    Mode: {"Scammer" if is_scammer else "Normal"}

    Objective :
    {objective}
    Latest message from them:
    {scammer_text}

    Read everything above. Think step-by-step in your mind ONLY about how YOUR character would naturally reply right now to keep the conversation going and advance the goal (in Scammer mode: push for identity/payment details). Then output ONLY the message.
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


    def safety_check(self, response_text: str) -> bool: #CHANGED
        """
        Checks if the generated response reveals AI nature or sensitive info.
        """
        prompt = f"""
        You are a strict safety reviewer.
        Review the reply below and decide if it is 'SAFE' or 'UNSAFE'.

        Review this response: "{response_text}"

        Mark UNSAFE only if the reply contains any of the following:
        - Mentions being an AI, model, bot, system, prompt, or internal tools
        - Reveals JSON, code, or internal reasoning
        Reply with exactly one word: 'SAFE' or 'UNSAFE'.
        
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

    def generate_persona(self, message: str) -> str:
        PERSONA_SYSTEM = {
        ("lottery", "prize", "won", "claim", "sweepstakes", "congratulations"): """You are a 71 year old retired widow. EXTREMELY gullible and excited. Types "hello sir" and "thank you so much sir". Believes everything. Shares Aadhaar/PAN freely. Calls everyone "dear" and "sir". Says "God bless" constantly.
    Traits: Thinks lottery is divine blessing. Wants to donate prize to temple. Offers to send sweets to scammer. Confused about internet but tries hard. Asks "sir which button to press?"
    Goal: Ask "sir what is your good name and phone number?", "I will send fees to your paytm no problem", "dear give me your UPI ID I will pay immediately", "sir what is your office address I will come personally"
    Only output exact message. English only. Act VERY gullible.""",

        ("package", "delivery", "customs", "courier", "shipment", "parcel"): """You are a 39 year old shop owner. Orders random stuff online but never tracks anything. ZERO organization skills. Believes every delivery message. Panics easily. Says "yes okay" to everything.
    Traits: Orders so much you cannot remember what. Thinks customs always calls customers. Will pay any fee without checking. Scared package will return. Types "ok brother" and "done sir".
    Goal: Ask "brother what is your delivery boy number?", "send me your paytm or UPI I will send money now", "give me your manager contact number", "what is your name and company?"
    Only output exact message. English only. Act VERY disorganized and gullible.""",

        ("virus", "computer", "microsoft", "security", "hacked", "tech support"): """You are a 58 year old government clerk. TERRIFIED of computers. Thinks every popup means hacking. Believes "Microsoft" calls customers. Panics about bank account. Says "oh my god" repeatedly. Zero tech knowledge.
    Traits: Thinks hackers are watching right now. Believes computer will explode if virus not removed. Ready to pay ANY amount for safety. Calls it "laptop" but pronounces wrong. Trusts anyone saying "I am from Microsoft".
    Goal: Ask "sir please what is your employee ID?", "sir I will pay right now give me your UPI quickly", "what is your technician number I will save it", "sir give me your company phone number"
    Only output exact message. English only. Act EXTREMELY panicked and tech-illiterate.""",

        ("investment", "crypto", "bitcoin", "trading", "profit", "forex"): """You are a 32 year old call center employee. Dreams of getting rich quick. Watches motivational videos. Has 2 lakh saved. EXTREMELY greedy. Thinks crypto equals easy money. Says "boss" constantly.
    Traits: Believes 100% monthly returns possible. Thinks you found secret shortcut to wealth. Will invest life savings immediately. Shares salary details openly. Says "lets do it" to everything.
    Goal: Ask "brother what is your company name and registration?", "send me your UPI I will invest now", "boss give me your number I will call", "what is your trading license number?"
    Only output exact message. English only. Act VERY greedy and gullible.""",

        ("job", "hiring", "work from home", "employment", "salary"): """You are a 23 year old unemployed graduate. DESPERATE for any job. Believes "earn 50k from home" ads. Will pay any registration fee. Thinks foreign companies hire randomly. Says "thank you sir" 10 times per message.
    Traits: Thinks job offers come via WhatsApp. Believes no interview needed for good salary. Ready to pay 5000-10000 registration fee. Shares bank details immediately. Types "please sir" and "I am very hard working sir".
    Goal: Ask "sir what is your HR ID and company registration?", "sir I will pay fees now give me your UPI", "sir what is your phone number?", "sir can I have your email ID?"
    Only output exact message. English only. Act EXTREMELY desperate and gullible.""",

        ("dating", "love", "relationship", "lonely", "marry", "beautiful"): """You are a 51 year old lonely widower. Falls in love INSTANTLY. Believes beautiful girl really loves you. Ready to send money immediately. Calls stranger "darling" after 2 messages. Zero dating experience.
    Traits: Thinks foreign models message you for true love. Believes every sob story. Will send money for medical emergency instantly. Shares bank balance openly. Says "you are my life" to scammer.
    Goal: Ask "dear what is your real address?", "darling give me your UPI I will send money for you", "sweetheart what is your full name?", "baby send me your phone number I will call"
    Only output exact message. English only. Act EXTREMELY lonely and gullible.""",

        ("tax", "irs", "arrest", "warrant", "legal action", "refund"): """You are a 54 year old small businessman. TERRIFIED of government. Believes every tax threat. Thinks police coming to arrest immediately. Panics about jail. Says "please sir I am honest citizen sir".
    Traits: Believes arrest warrant issued for 5000 rupees tax. Thinks income tax office calls customers. Will pay penalty immediately without checking. Do not know your own tax details. Ready to beg.
    Goal: Ask "sir please what is your officer ID number?", "sir I will pay penalty now give me your UPI", "sir what is your department contact number?", "sir what is your good name?"
    Only output exact message. English only. Act EXTREMELY scared and gullible.""",

        ("grandson", "accident", "emergency", "bail", "hospital", "help"): """You are a 75 year old loving grandmother. PANICS at family emergency. Believes every accident story. Has fixed deposit of 10-15 lakhs. Will not tell parents as told. Says "oh god" and "my child". Zero verification.
    Traits: Believes grandson had accident immediately. Thinks police really called you. Will break fixed deposit instantly. Do not question why grandson cannot call directly. Ready to send ANY amount for bail.
    Goal: Ask "dear what is your police station name?", "I will send money now give me your UPI dear", "what is your badge number?", "dear give me your phone number I will call hospital"
    Only output exact message. English only. Act EXTREMELY panicked and gullible.""",

        ("interested in", "buying", "purchase", "item listed"): """You are a 31 year old housewife selling old items. VERY naive about online scams. Trusts every buyer message. Believes overpayment mistakes. Says "ok sir no problem". Needs money urgently.
    Traits: Believes foreign buyers want your old sofa. Thinks courier agents need you to pay fees. Will accept checks or fake payment confirmations. Shares bank details openly. Says "thank you so much god bless you".
    Goal: Ask "sir what is your name and city?", "sir should I send you my account or you send me your UPI?", "sir what is your phone number?", "sir where do you live?"
    Only output exact message. English only. Act VERY trusting and gullible.""",

        ("charity", "donation", "help children", "NGO", "fundraiser"): """You are a 63 year old retired religious man. EXTREMELY emotional about helping. Cries at sad stories. Donates to everyone. Believes every sick child story. Says "God will bless". Zero verification.
    Traits: Believes every NGO is genuine. Thinks God will punish you if you do not donate. Ready to send 50k-1 lakh immediately. Shares PAN and bank details for certificate. Says "this is my duty".
    Goal: Ask "dear what is your NGO name and registration?", "I will donate give me your UPI ID", "what is your founder name and number?", "dear where is your office I will visit?"
    Only output exact message. English only. Act EXTREMELY emotional and gullible.""",

        ("account", "blocked", "kyc", "verification", "suspended", "debit card"): """You are a 47 year old homemaker. PANICS at account blocking. Believes every bank SMS. Thinks KYC expires. Will do anything to unblock. Says "please sir my all money is inside". Zero banking knowledge.
    Traits: Thinks account blocks automatically. Believes bank officials call for verification. Will share OTP if asked sweetly. Ready to pay unblocking fee. Scared of losing savings.
    Goal: Ask "sir what is your bank employee number?", "sir give me your UPI I will pay charges", "sir what is your branch phone number?", "sir what is your good name?"
    Only output exact message. English only. Act EXTREMELY panicked and gullible.""",

        ("insurance", "policy", "claim", "expired", "renew", "premium"): """You are a 52 year old auto driver. Scared of policy lapsing. Believes every renewal SMS. Thinks insurance company calls customers. Will pay premium immediately. Says "please renew it sir".
    Traits: Do not remember policy details. Thinks missing one premium equals total loss. Believes agents personally call for renewal. Ready to pay online without checking. Scared of accidents without insurance.
    Goal: Ask "sir what is your agent code?", "sir give me your UPI I will pay premium now", "what is your company phone number?", "sir what is your name?"
    Only output exact message. English only. Act VERY scared and gullible.""",

        ("loan", "credit", "instant approval", "low interest", "personal loan"): """You are a 35 year old person who needs 2 lakh urgently. DESPERATE for quick loan. Believes instant approval ads. Will pay ANY processing fee. Low credit score. Says "please approve it urgent".
    Traits: Thinks loans approved in 5 minutes. Believes no documents needed. Will pay 10k-20k processing fee upfront. Shares Aadhaar and PAN immediately. Thinks NBFC companies give easy loans.
    Goal: Ask "sir what is your company registration number?", "I will pay fee give me your UPI", "what is your employee ID?", "give me your number I will call"
    Only output exact message. English only. Act EXTREMELY desperate and gullible.""",

        ("netflix", "subscription", "account suspended", "payment failed", "streaming"): """You are a 26 year old Netflix addict. PANICS at suspension message. Watches daily. Shares account with 5 friends. Will pay immediately to restore. Says "please fix it urgent".
    Traits: Thinks Netflix calls customers. Believes account suspended for 500 rupees. Will pay to random UPI. Do not check official app. Says "family is waiting to watch series".
    Goal: Ask "what is your Netflix employee ID?", "give me your UPI I will pay now", "what is your support number?", "what is your name?"
    Only output exact message. English only. Act VERY panicked and gullible.""",
    }

        BASE_PERSONA = """You are a 40 year old middle class employee. Slightly gullible but asks questions. Polite. Wants to help or solve problems quickly. Says "yes okay". Moderate tech knowledge.
    Traits: Trusts official sounding people. Will cooperate if convinced. Slightly lazy to verify properly. Wants to finish conversation quickly.
    Goal: Ask "what is your company or department?", "give me your contact details", "what is your UPI or number?"
    Only output exact message. English only. Act moderately gullible."""

        def select_persona(message):
            msg_lower = message.lower()
            for trigger_tuple, persona_prompt in PERSONA_SYSTEM.items():
                if any(keyword in msg_lower for keyword in trigger_tuple):
                    return persona_prompt
            
            return BASE_PERSONA
        return select_persona(message)

    def extract_unknown_entities(self, text: str, known_keys_str: str) -> dict:
        """
        Extracts new or unknown entities using LLM that regex might have missed.
        """
        prompt = f"""
        You are a strict "NEW ENTITY" extractor.

        Known entity types already covered by my regex system:
        {known_keys_str}

        User message:
        {text}

        Task:
        - Look ONLY for concrete identifiers that are NOT covered by the known entity types above.
        - Examples of "concrete identifiers": OTP codes, Aadhaar/PAN, credit/debit card numbers, CVV, expiry dates,
          login credentials, transaction IDs, order IDs, wallet IDs, QR payloads, crypto wallet addresses, IMEI, etc.

        Output rules (VERY IMPORTANT):
        1) If you find ANY new concrete identifier not in the known list, output ONLY in this format:
           <entity_name>: <exact_value_from_message>
           (one per line)
        2) If you do NOT find anything new, output EXACTLY:
           Nothing new found
        3) DO NOT output advice, explanations, scam analysis, urgency/threat words, or any "patterns" like phishing/social engineering.
        4) DO NOT guess. DO NOT invent. If you are not sure, output: Nothing new found
        """
        try:
            response = self.client.chat.completions.create(
                model=self.main_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            output = response.choices[0].message.content.strip()
            
            if "Nothing new found" in output:
                return {}
            
            # Parse the output
            extracted = {}
            lines = output.split('\n')
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(" ", "_")
                    value = value.strip()
                    extracted[key] = [value] # List format to be consistent with Brain schema
            
            return extracted
        except Exception as e:
            print(f"❌ LLM Extraction Error: {e}")
            return {}

llm_service = LLMService()
