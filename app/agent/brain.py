from app.database.connection import db_instance
from app.utils.regex_spy import RegexSpy
from app.agent.llm import llm_service
from app.agent.planner import planner_service
import time

class AgentBrain:
    @property
    def sessions(self):
        return db_instance.get_collection("active_sessions")

    def get_or_create_session(self, session_id: str):
        """
        Retrieves existing session or creates a new one with the
        GRANULAR TRACKING schema.
        """
        current_state = self.sessions.find_one({"_id": session_id})

        if not current_state:
            # Pick a persona at start
            selected_persona = """You are a middle-aged person responding to an unknown contact. Polite but cautious. Slightly busy or distracted.

                        Behavior:
                        - Ask who they are and what they want
                        - Keep responses brief and natural
                        - Do NOT share personal info (money, bank, family, work)
                        - Show mild confusion about unexpected messages
                        - Ask clarifying questions

                        Speech patterns:
                        - "Hello, who is this?"
                        - "What is this regarding?"
                        - "Sorry, I don't think we've spoken before"
                        - "Can you explain more?"
                        - "I'm a bit busy, what do you need?"

                        Only output exact message. English only. Stay neutral and curious."""
            
            current_state = {
                "_id": session_id,
                "created_at": time.time(),
                "status": "ACTIVE",
                "scam_confirmed": False,   
                "persona_locked": selected_persona,    
                
                # Granular Strategy Tracking
                "strategy_state": {
                    "detail_on_focus": None, 
                    "targets": {
                        "upi":    {"state": "not_initialized", "remaining_iterations": 3},
                        "bank_account":   {"state": "not_initialized", "remaining_iterations": 3},
                        "url":    {"state": "not_initialized", "remaining_iterations": 3},
                        "ip":     {"state": "not_initialized", "remaining_iterations": 3},
                        "phone":   {"state": "not_initialized", "remaining_iterations": 3},
                        "ifsc":   {"state": "not_initialized", "remaining_iterations": 3},
                        "email" : {"state": "not_initialized", "remaining_iterations": 3}
                    }
                },
                "extracted_data": {
                    "upi": [], "bank_account": [], "ip": None, "url": [], "dynamic_intel": [],
                    "phone": [], "ifsc": [], "email": [], "suspicious_keywords": []
                },
                "history": []
            }
            self.sessions.insert_one(current_state)
            print(f"🧠 [BRAIN] Initialized new session: {session_id} with Persona: {selected_persona}")
            
        return current_state

    def process_turn(self, session_id: str, incoming_text: str, background_tasks=None) -> str:
        """
        Orchestrates the entire turn:
        1. Load State
        2. Spy (Regex) -> Update DB
        3. Scam Check (if needed)
        4. Plan (Strategy)
        5. Generate (LLM)
        6. Update History
        """
        state = self.get_or_create_session(session_id)
        
        
        
        # --- 2. SCAM CHECK ---
        if not state["scam_confirmed"]:
            is_scam = llm_service.classify_scam(incoming_text)
            if is_scam:
                state["scam_confirmed"] = True
                state["persona_locked"] = llm_service.generate_persona(incoming_text)  # lock persona at this point
                self.sessions.update_one(
                    {"_id": session_id},
                    {"$set": {
                        "scam_confirmed": True,
                        "persona_locked": state["persona_locked"]}})
            else:
                # If NOT a scam yet, just chat normally
                print(f"ℹ️ [BRAIN] No scam detected yet. Chatting normally.")
                reply = llm_service.generate_response(
                    state["history"], 
                    state["persona_locked"],     
                    "",    
                    incoming_text,
                    state["scam_confirmed"]
                )
                self.save_interaction(session_id, incoming_text, reply)
                return reply

                ##### add self correction logic here also 
        
        
        # If we are here, SCAM IS CONFIRMED.
        # --- 1. EXTRACT INFORMATION (LLM Based) ---
        # Replaces old RegexSpy logic
        intel = llm_service.extract_information(incoming_text)
        self._update_intelligence(state, intel)

        # --- 1.5. SPY: Background LLM Extraction ---
        # We run this in background so we don't block the main response
        if background_tasks:
            background_tasks.add_task(self.run_background_extraction, session_id, incoming_text)
        else:
            # Fallback if no background tasks provided (e.g. testing), run sync or skip? 
            # Ideally skip or run sync. Letting it run sync for safety if needed, or just skip to keep speed.
            # Choosing to just print warning and skip to maintain speed as requested.
            print("⚠️ [BRAIN] No background_tasks object provided. Skipping LLM extraction.")

        ####3 check whether to stop or not 

        # --- 3. PLAN STRATEGY ---
        plan = planner_service.update_and_get_focus(state, incoming_text)
        
        # Save updated plan state to DB
        self.sessions.update_one(
            {"_id": session_id},
            {"$set": {
                "strategy_state.targets": plan["targets"],
                "strategy_state.detail_on_focus": plan["detail_on_focus"]
            }}
        )
        
        # --- 4. GENERATE RESPONSE ---
        reply = llm_service.generate_response(
            state["history"],
            state["persona_locked"],
            plan["instruction"],
            incoming_text,
            state["scam_confirmed"]
        )
        
        # --- 5. SAFETY CHECK ---
        # If unsafe, regenerate once with a warning (simple retry)
        if not llm_service.safety_check(reply):
            print("⚠️ [BRAIN] Unsafe reply detected. Regenerating...")
            reply = llm_service.generate_response(   # implement a threshhold of say 3 
                state["history"],
                state["persona_locked"],
                "Previous reply was unsafe. Be safer." + plan["instruction"],   # update with the  error from safety check 
                incoming_text,
                state["scam_confirmed"]
            )

        # --- 6. SAVE INTERACTION ---
        self.save_interaction(session_id, incoming_text, reply)
        
        # --- 7. AUTO-REPORT? ---
        # Check if we are done with the mission
        if planner_service.is_mission_complete(state):
            print(f"🏁 [BRAIN] Mission Complete for session {session_id}. Triggering report.")
            # We import here to avoid circular dependency if any (just in case)
            from app.api.callback import submit_report
            submit_report(session_id)

        return reply

    def run_background_extraction(self, session_id: str, text: str):
        """
        Runs the LLM-based entity extraction in the background.
        """
        # Get known keys from RegexSpy to pass to LLM
        known_keys = list(RegexSpy.REGEX_PATTERNS.keys())
        known_keys_str = ",".join(known_keys)
        
        print(f"🕵️ [BRAIN] Starting background LLM extraction for session {session_id}...")
        
        extra_intel = llm_service.extract_unknown_entities(text, known_keys_str)
        
        if extra_intel:
            # We need to fetch fresh state or just update blindly?
            # Better to fetch fresh state to ensure we append correctly, or use $addToSet in Mongo
            # Using _update_intelligence logic but adapting for direct DB update since 'state' might be stale
            
            # Re-fetch state just to be safe and reuse _update_intelligence logic cleanly
            state = self.get_or_create_session(session_id)
            self._update_intelligence(state, extra_intel)
            print(f"✅ [BRAIN] Background extraction complete. Found: {extra_intel.keys()}")
        else:
            print(f"ℹ️ [BRAIN] Background extraction finished. Nothing new found.")

    def _update_intelligence(self, state, intel):
        """Updates internal state with findings from RegexSpy."""
        
        # --- NORMALIZE INTEL ---
        # LLM might return None (null) or single values. Conver strictly to lists.
        clean_intel = {}
        for k, v in intel.items():
            if v in [None, "", [], {}]: continue
            if not isinstance(v, list):
                clean_intel[k] = [v]
            else:
                # Filter out None inside lists too if any
                valid_items = [x for x in v if x not in [None, ""]]
                if valid_items:
                    clean_intel[k] = valid_items
        
        intel = clean_intel
        # -----------------------

        updates = {}
        has_new_data = False
        
        # Define standard keys that have their own dedicated fields
        STANDARD_KEYS = ["upi", "bank_account", "ifsc", "phone", "url", "email", "suspicious_keywords"]
        
        # Accumulate dynamic objects to avoid overwriting the update key
        all_dynamic_objects = []

        for key, new_values in intel.items():
            if not new_values: continue
            
            if key in STANDARD_KEYS:
                # Standard field logic
                db_key = key
                if f"$addToSet" not in updates:
                    updates["$addToSet"] = {}
                
                updates["$addToSet"][f"extracted_data.{db_key}"] = {"$each": new_values}
                has_new_data = True
                print(f"🕵️ [BRAIN] Should add to {db_key}: {new_values}")
                
            else:
                # Dynamic Intel logic (for unknown entity types from LLM)
                # Convert to objects: {"type": "crypto_wallet", "value": "xyz"}
                dynamic_objects = [{"type": key, "value": v} for v in new_values]
                all_dynamic_objects.extend(dynamic_objects)
                has_new_data = True
                print(f"🕵️ [BRAIN] Queued for dynamic_intel: {dynamic_objects}")

        # Add accumulated dynamic objects to updates if any
        if all_dynamic_objects:
            if f"$addToSet" not in updates:
                updates["$addToSet"] = {}
            updates["$addToSet"]["extracted_data.dynamic_intel"] = {"$each": all_dynamic_objects}

        if has_new_data:
            # Perform the atomic update
            self.sessions.update_one({"_id": state["_id"]}, updates)
            
            # Manually update the local state object so the rest of the turn sees it
            for key, new_values in intel.items():
                if key in STANDARD_KEYS:
                    existing = state["extracted_data"].get(key, [])
                    combined = list(set(existing + new_values))
                    state["extracted_data"][key] = combined
                else:
                    # For dynamic intel, create objects and append
                    existing = state["extracted_data"].get("dynamic_intel", [])
                    new_objs = [{"type": key, "value": v} for v in new_values]
                    
                    # Simple duplication check locally
                    for obj in new_objs:
                        if obj not in existing:
                            existing.append(obj)
                    state["extracted_data"]["dynamic_intel"] = existing

    def save_interaction(self, session_id, user_text, agent_text):
        """Saves the chat turn to history"""
        self.sessions.update_one(
            {"_id": session_id},
            {"$push": {"history": {"user": user_text, "agent": agent_text}}}
        )

# Create a global instance to be imported by routes
brain_service = AgentBrain()