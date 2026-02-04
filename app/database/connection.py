from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from app.core.config import settings
import sys

class Database:
    client: MongoClient = None
    db = None

    def connect(self):
        """Establishes the connection to MongoDB."""
        if not self.client:
            try:
                print("🔌 Connecting to MongoDB...")
                self.client = MongoClient(settings.MONGO_URI)
                self.db = self.client[settings.DB_NAME]
                
                # Test the connection specifically
                self.client.admin.command('ping')
                print("✅ MongoDB Connection Successful!")
                
            except ConnectionFailure as e:
                print(f"❌ MongoDB Connection Failed: {e}")
                sys.exit(1) # Stop the app if DB fails

    def disconnect(self):
        """Closes the connection."""
        if self.client:
            self.client.close()
            print("🔌 MongoDB Connection Closed.")

    def get_collection(self, collection_name):
        """Helper to get a specific collection."""
        if self.db is not None:
            return self.db[collection_name]
        else:
            raise ConnectionError("Database not connected. Call connect() first.")

# Create a global instance
db_instance = Database()