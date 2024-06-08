from bson import ObjectId
from datetime import datetime

class ItemsManager:
    def __init__(self, mongo_client):
        self.db = mongo_client["drip"]
        self.items_collection = self.db["items"]
        self.liked_items_collection = self.db["liked_items"]
        self.wishlist_items_collection = self.dh["wishlist_items"]

    def get_all_items(self):
        items = list(self.items_collection.find({}))
        return items

    def get_liked_items(self, user_id):
        user_object_id = ObjectId(user_id)
        liked_items = list(self.liked_items_collection.aggregate([
            { "$match": { "user_id": user_object_id } },
            {
                "$lookup": {
                    "from": "items",
                    "localField": "item_id",
                    "foreignField": "_id",
                    "as": "item"
                }
            },
            { "$unwind": "$item" },
            { "$project": { "item": 1, "_id": 0 } },
            { "$replaceRoot": { "newRoot": "$item" } }
        ]))
        return liked_items

    def create_liked_item(self, item_id, user_id):
        item_object_id = ObjectId(item_id)
        user_object_id = ObjectId(user_id)
        current_time = datetime.utcnow()
        result = self.liked_items_collection.update_one(
            { "item_id": item_object_id, "user_id": user_object_id },
            { "$setOnInsert": { "item_id": item_object_id, "user_id": user_object_id, "date_liked": current_time } },
            upsert=True
        )
        return "Item already liked" if result.matched_count > 0 else "Item was liked"

    def delete_liked_item(self, item_id, user_id):
        item_object_id = ObjectId(item_id)
        user_object_id = ObjectId(user_id)
        self.liked_items_collection.delete_one({ "item_id": item_object_id, "user_id": user_object_id })
        return "Sucessfully unliked item"

    def get_wishlist_items(self, user_id):
        user_object_id = ObjectId(user_id)
        wishlist_items = list(self.wishlist_items_collection.aggregate([
            { "$match": { "user_id": user_object_id } },
            {
                "$lookup": {
                    "from": "items",
                    "localField": "item_id",
                    "foreignField": "_id",
                    "as": "item"
                }
            },
            { "$unwind": "$item" },
            { "$project": { "item": 1, "_id": 0 } },
            { "$replaceRoot": { "newRoot": "$item" } }
        ]))
        return wishlist_items

    def create_wishlist_item(self, item_id, user_id):
        item_object_id = ObjectId(item_id)
        user_object_id = ObjectId(user_id)
        current_time = datetime.utcnow()
        result = self.wishlist_items_collection.update_one(
            { "item_id": item_object_id, "user_id": user_object_id },
            { "$setOnInsert": { "item_id": item_object_id, "user_id": user_object_id, "date_liked": current_time } },
            upsert=True
        )
        return "Item already in wishlist" if result.matched_count > 0 else "Item was added to wishlist"

    def delete_wishlist_item(self, item_id, user_id):
        item_object_id = ObjectId(item_id)
        user_object_id = ObjectId(user_id)
        self.wishlist_items_collection.delete_one({ "item_id": item_object_id, "user_id": user_object_id })
        return "Sucessfully removed item from wishlist"
