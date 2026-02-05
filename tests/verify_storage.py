import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import after path fix
from app.agent.brain import brain_service

class TestStorageLogic(unittest.TestCase):
    def setUp(self):
        # We need to mock the db_instance used by the property, OR patch the property itself
        # Let's patch the property on the class or instance. 
        # Since it's a property on the instance's class, we can mock db_instance.
        
        # Simpler: mock db_instance in the brain module if possible, 
        # BUT brain imports db_instance directly.
        
        # Let's use patch context manager in tests or setup patches there.
        # However, for simplicity, we can just patch `app.agent.brain.db_instance`
        pass

    @patch('app.agent.brain.db_instance')
    def test_update_intelligence_standard(self, mock_db):
        print("\n--- Testing Standard Key Update ---")
        # Setup mock collection
        mock_collection = MagicMock()
        mock_db.get_collection.return_value = mock_collection
        
        state = {"_id": "test_session", "extracted_data": {"upi": []}}
        intel = {"upi": ["alice@bank"]}
        
        brain_service._update_intelligence(state, intel)
        
        # Verify call args
        args = mock_collection.update_one.call_args
        # args[0] is query, args[1] is update
        update_op = args[0][1]
        
        print(f"Update Op: {update_op}")
        self.assertIn("$addToSet", update_op)
        self.assertIn("extracted_data.upi", update_op["$addToSet"])
        self.assertEqual(update_op["$addToSet"]["extracted_data.upi"]["$each"], ["alice@bank"])
        print("✅ Standard key update correct")

    @patch('app.agent.brain.db_instance')
    def test_update_intelligence_dynamic(self, mock_db):
        print("\n--- Testing Dynamic Intel Update ---")
        mock_collection = MagicMock()
        mock_db.get_collection.return_value = mock_collection
        
        state = {"_id": "test_session", "extracted_data": {"dynamic_intel": []}}
        # Unknown key from LLM
        intel = {"crypto_wallet": ["1A1zP1..."], "otp": ["123456"]}
        
        brain_service._update_intelligence(state, intel)
        
        args = mock_collection.update_one.call_args
        update_op = args[0][1]
        
        print(f"Update Op: {update_op}")
        self.assertIn("$addToSet", update_op)
        self.assertIn("extracted_data.dynamic_intel", update_op["$addToSet"])
        
        # Check if values are objects
        added_items = update_op["$addToSet"]["extracted_data.dynamic_intel"]["$each"]
        
        expected_crypto = {"type": "crypto_wallet", "value": "1A1zP1..."}
        expected_otp = {"type": "otp", "value": "123456"}
        
        # The order in 'each' depends on iteration order of dict, which is insertion order in py3.7+
        # We just check existence
        self.assertIn(expected_crypto, added_items)
        self.assertIn(expected_otp, added_items)
        print("✅ Dynamic intel update correct (stored as objects)")

if __name__ == '__main__':
    unittest.main()
