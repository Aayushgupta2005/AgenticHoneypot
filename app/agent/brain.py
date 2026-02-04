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
            selected_persona = llm_service.generate_persona()
            
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

    def process_turn(self, session_id: str, incoming_text: str) -> str:
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
                print(f"🚨 [BRAIN] Scam Detected in session {session_id}")
            else:
                # If NOT a scam yet, just chat normally
                print(f"ℹ️ [BRAIN] No scam detected yet. Chatting normally.")
                reply = llm_service.generate_response(
                    state["history"], 
                    "Friendly User", 
                    "Chat casually",          
                    incoming_text
                )
                self.save_interaction(session_id, incoming_text, reply)
                return reply

                ##### add self correction logic here also 
        
        
        # If we are here, SCAM IS CONFIRMED.
        # --- 1. SPY: Regex Extraction ---
        intel = RegexSpy.extract_intelligence(incoming_text)
        self._update_intelligence(state, intel)

        ####3 check whether to stop or not 

        # --- 3. PLAN STRATEGY ---
        plan = planner_service.update_and_get_focus(state)
        
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
            incoming_text
        )
        
        # --- 5. SAFETY CHECK ---
        # If unsafe, regenerate once with a warning (simple retry)
        if not llm_service.safety_check(reply):
            print("⚠️ [BRAIN] Unsafe reply detected. Regenerating...")
            reply = llm_service.generate_response(   # implement a threshhold of say 3 
                state["history"],
                state["persona_locked"],
                "Previous reply was unsafe. Be safer.",   # update with the  error from safety check 
                incoming_text
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

    def _update_intelligence(self, state, intel):
        """Updates internal state with findings from RegexSpy."""
        updates = {}
        has_new_data = False
        
        for key, new_values in intel.items():
            if not new_values: continue
            
            # Key in DB might differ slightly or be same
            db_key = key # Schema matches mostly
            if key == "suspicious_keywords": db_key = "suspicious_keywords" # matches
            
            # Simple list extension
            existing = state["extracted_data"].get(db_key, [])
            # Avoid duplicates
            clean_new = [v for v in new_values if v not in existing]
            
            if clean_new:
                has_new_data = True
                updates[f"extracted_data.{db_key}"] = existing + clean_new
                print(f"🕵️ [BRAIN] Captured new {key}: {clean_new}")

        if has_new_data:
            self.sessions.update_one({"_id": state["_id"]}, {"$set": updates})
            # Also update local state object for this turn
            for k, v in updates.items():
                # k is like "extracted_data.upi", v is the new list
                field = k.split(".")[1]
                state["extracted_data"][field] = v

    def save_interaction(self, session_id, user_text, agent_text):
        """Saves the chat turn to history"""
        self.sessions.update_one(
            {"_id": session_id},
            {"$push": {"history": {"user": user_text, "agent": agent_text}}}
        )

# Create a global instance to be imported by routes
brain_service = AgentBrain()