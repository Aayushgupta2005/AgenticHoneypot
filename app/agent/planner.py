from app.agent.llm import llm_service
class StrategicPlanner:
    def __init__(self):
        # Priority Order: What do we want most?
        self.priority_list = [
            "upi", 
            "bank_account", 
            "url", 
            "ip"
        ]
    def update_and_get_focus(self, state, incoming_text):
        """
        Analyzes the granular state, updates iterations, and decides 
        the current tactical objective.
        """
        strategy_state = state.get("strategy_state", {})
        targets = strategy_state.get("targets", {})
        current_focus = strategy_state.get("detail_on_focus")

        # 1. CHECK CURRENT FOCUS (If we had one)
        if current_focus:
            target_info = targets.get(current_focus)
            
            # Did we just succeed? (Check if extracted_data has this field)
            # logic: if state['extracted_data']['upi'] is not empty, success.
            is_success = self._check_success(state, current_focus)
            
            if is_success:
                targets[current_focus]["state"] = "success"
                targets[current_focus]["remaining_iterations"] = 0
                current_focus = None # Reset focus to find new one
                print(f"🎯 [PLANNER] Success captured for {current_focus}")
            else:
                # Decrement iterations because we tried and failed this turn
                if targets[current_focus]["remaining_iterations"] > 0:
                    targets[current_focus]["remaining_iterations"] -= 1
                    targets[current_focus]["state"] = "initialized"
                
                # If runs out of tries, give up
                if targets[current_focus]["remaining_iterations"] <= 0:
                    targets[current_focus]["state"] = "failure"
                    current_focus = None # Reset focus
                    print(f"⚠️ [PLANNER] Gave up on {current_focus}")

        # 2. SELECT NEW FOCUS (If needed)
        if not current_focus:
            # for goal in self.priority_list:
            #     goal_state = targets.get(goal)
            #     # Find the first one that is NOT success and NOT failure
            #     if goal_state["state"] not in ["success", "failure"]:
            #         current_focus = goal
            #         targets[current_focus]["state"] = "initialized"
            #         break

            current_focus = llm_service.get_instruction_from_llm(state, incoming_text, objective=["upi","bank_account","url","phone","email","ifsc"])
            targets[current_focus]["state"] = "initialized"
            targets[current_focus]["remaining_iterations"] = 3
            instruction = self._get_instruction_text(current_focus)
        
        # 3. GENERATE INSTRUCTION FOR LLM
        # instruction = self._get_instruction_text(current_focus)
        instruction = ""

        # Return updated sub-state and the prompt instruction
        return {
            "detail_on_focus": current_focus,
            "targets": targets,
            "instruction": instruction
        }

    def _check_success(self, state, focus_key):
        """Helper to see if we actually got the data"""
        data = state.get("extracted_data", {})
        mapping = {
            "upi": "upi",
            "bank_account": "bank_account",
            "url": "url",
            "ip": "ip"
        }
        key_in_db = mapping.get(focus_key)
        
        if not key_in_db: return False
        
        # If list is not empty (or value not None), we succeeded!
        val = data.get(key_in_db)
        return bool(val)

    def _get_instruction_text(self, focus):
        """Returns the specific prompt for the LLM"""
        if not focus:
            return "OBJECTIVE: Stall for time. Ask generic questions."
            # but aso analyse the current scenario , for example if the scammer is asking for otp and you just ask for upi because you are searching for it then it will be a wrong move so please first handle this then ask for upi
        prompts = {
            "upi": "OBJECTIVE: Ask for their UPI ID (e.g., GooglePay/PhonePe) so you can send money. ",
            "bank_account": "OBJECTIVE: Ask for their Bank Account Number and IFSC code.",
            "ifsc": "OBJECTIVE: Ask them to confirm or resend the IFSC code due to a bank validation issue.",
            "phone": "OBJECTIVE: Ask for their phone/WhatsApp number to coordinate the payment or call for confirmation.",
            "url": "OBJECTIVE: Ask for a payment link or QR code.",
            "email": "OBJECTIVE: Ask for their email ID to send a payment receipt or confirmation.",
            "ip": "OBJECTIVE: Send them the 'Payment Receipt' link (Canary Token) and ask them to verify it."
        }
        return prompts.get(focus, "OBJECTIVE: Chat normally.")

    def is_mission_complete(self, state):
        """
        Checks if we have exhausted all our goals (Success or Failure).
        """
        strategy_state = state.get("strategy_state", {})
        targets = strategy_state.get("targets", {})
        
        # Check if ALL priority goals are terminal
        for goal in self.priority_list:
            status = targets.get(goal, {}).get("state")
            if status not in ["success", "failure"]:
                return False # Still working on 'goal' (it's initialized or not_initialized)
        
        return True

planner_service = StrategicPlanner()