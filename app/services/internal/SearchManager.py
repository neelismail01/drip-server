from bson import ObjectId
from datetime import datetime

class SearchManager():
    def __init__(self, mongo_client):
        self.db = mongo_client["drip"]
        self.searches_collection = self.db["searches"]
        self.items_collection = self.db["items"]
        self.outfits_collection = self.db["outfits"]
        self.users_collection = self.db["users"]