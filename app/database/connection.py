
from pymongo import MongoClient
# from app.core.config import settings

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    def connect(self):
        # self.client = MongoClient(settings.MONGODB_URL)
        # self.db = self.client[settings.DB_NAME]
        pass

    def get_db(self):
        return self.db

db = MongoDB()
