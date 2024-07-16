from bson import ObjectId
from datetime import datetime
from app.utils.constants import (
    USER_SEARCH_RESULT_TYPE,
    BRAND_SEARCH_RESULT_TYPE,
    SUGGESTED_SEARCH_RESULT_TYPE
)

class SearchManager():
    def __init__(self, mongo_client):
        self.db = mongo_client["drip"]
        self.searches_collection = self.db["searches"]
        self.items_collection = self.db["items"]
        self.outfits_collection = self.db["outfits"]
        self.users_collection = self.db["users"]
        self.brands_collection = self.db["brands"]

    def search_users(self, query):
        users = list(self.users_collection.aggregate([
            {
                "$search": {
                    "index": "users_index",
                    "compound": {
                        "should": [
                            { "autocomplete": { "query": query, "path": "username" } },
                            { "autocomplete": { "query": query, "path": "name" } }
                        ]
                    }
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "email": 1,
                    "name": 1,
                    "profile_complete": 1,
                    "date_created": 1,
                    "profile_picture": 1,
                    "username": 1,
                    "preference": 1,
                    "birthdate": 1,
                    "score": { "$meta": "searchScore" },
                    "type": USER_SEARCH_RESULT_TYPE
                }
            },
            { "$sort": { "score": -1 } },
            { "$limit": 5 }
        ]))
        return users

    def search_brands(self, query):
        brands = list(self.brands_collection.aggregate([
            {
                "$search": {
                    "index": "brands_index",
                    "compound": {
                        "should": [
                            { "autocomplete": { "query": query, "path": "name" } }
                        ]
                    }
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "domain": 1,
                    "name": 1,
                    "profile_picture": 1,
                    "score": { "$meta": "searchScore" },
                    "type": BRAND_SEARCH_RESULT_TYPE
                }
            },
            { "$sort": { "score": -1 } },
            { "$limit": 5 }
        ]))
        return brands

    def add_search(self, user_id, profile_id, query, query_type, autocomplete):
        user_object_id = ObjectId(user_id)
        profile_object_id = ObjectId(profile_id) if profile_id else None
        current_time = datetime.utcnow()
        self.searches_collection.insert_one({
            "user_id": user_object_id,
            "profile_id": profile_object_id,
            "query": query,
            "query_type": query_type,
            "autocomplete": autocomplete,
            "date_created": current_time,
        })
    