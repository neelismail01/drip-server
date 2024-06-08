from bson import ObjectId
from datetime import datetime

class OutfitsManager:
    def __init__(self, mongo_client):
        self.db = mongo_client["drip"]
        self.outfits_collection = self.db["outfits"]
        self.liked_outfits_collection = self.db["liked_outfits"]
        self.wishlist_outfits_collection = self.db["wishlist_outfits"]

    def get_outfits_for_user(self, user_id):
        user_object_id = ObjectId(user_id)
        outfits = list(self.outfits_collection.aggregate([
            { "$match": {"user_id": user_object_id } },
            {
                "$lookup": {
                    "from": "items",
                    "localField": "items",
                    "foreignField": "_id",
                    "as": "items"
                }
            }
        ]))
        return outfits

    def create_outfit(self, user_id, items, media_urls, name, caption, tags):
        item_ids = [ObjectId(item["_id"]) for item in items]
        existing_outfit = self.outfits_collection.find_one({'items': item_ids})
        if existing_outfit:
            return "Outfit already found in the database"

        user_object_id = ObjectId(user_id)
        current_time = datetime.utcnow()
        self.outfits_collection.insert_one({
            "user_id": user_object_id,
            "items": item_ids,
            "images": media_urls,
            "name": name,
            "caption": caption,
            "tags": tags,
            "date_created": current_time
        })
        return "Created outfit"    

    def get_liked_outfits(self, user_id):
        user_object_id = ObjectId(user_id)
        liked_outfits = list(self.liked_outfits_collection.find([
            { "$match": {"user_id": user_object_id } },
            {
                "$lookup": {
                    "from": "items",
                    "localField": "items",
                    "foreignField": "_id",
                    "as": "items"
                }
            }
        ]))
        return liked_outfits

    def created_liked_outfit(self, user_id, outfit_id):
        outfit_object_id = ObjectId(outfit_id)
        user_object_id = ObjectId(user_id)
        current_time = datetime.utcnow()
        result = self.liked_outfits_collection.update_one(
            { "outfit_id": outfit_object_id, "user_id": user_object_id },
            { "$setOnInsert": { "outfit_id": outfit_object_id, "user_id": user_object_id, "date_liked": current_time } },
            upsert=True
        )
        return "Outfit already liked" if result.matched_count > 0 else "Outfit was liked"

    def delete_liked_outfit(self, user_id, outfit_id):
        outfit_object_id = ObjectId(outfit_id)
        user_object_id = ObjectId(user_id)
        self.liked_outfits_collection.delete_one({ "outfit_id": outfit_object_id, "user_id": user_object_id })
        return "Sucessfully unliked outfit"

    def get_wishlist_outfits(self, user_id):
        user_object_id = ObjectId(user_id)
        wishlist_items = list(self.wishlist_outfits_collection.aggregate([
            { "$match": { "user_id": user_object_id } },
            {
                "$lookup": {
                    "from": "outfits",
                    "localField": "outfit_id",
                    "foreignField": "_id",
                    "as": "outfit"
                }
            },
            { "$unwind": "$outfit" },
            { "$project": { "outfit": 1, "_id": 0 } },
            { "$replaceRoot": { "newRoot": "$outfit" } },
            { "$lookup": {
                    "from": "items",
                    "localField": "items",
                    "foreignField": "_id",
                    "as": "items"
                }
            }
        ]))
        return wishlist_items

    def create_wishlist_outfit(self, user_id, outfit_id):
        outfit_object_id = ObjectId(outfit_id)
        user_object_id = ObjectId(user_id)
        current_time = datetime.utcnow()
        result = self.wishlist_outfits_collection.update_one(
            { "outfit_id": outfit_object_id, "user_id": user_object_id },
            { "$setOnInsert": { "outfit_id": outfit_object_id, "user_id": user_object_id, "date_liked": current_time } },
            upsert=True
        )
        return "Outfit already in wishlist" if result.matched_count > 0 else "Outfit added to wishlist"

    def delete_wishlist_outfit(self, user_id, outfit_id):
        outfit_object_id = ObjectId(outfit_id)
        user_object_id = ObjectId(user_id)
        self.wishlist_outfits_collection.delete_one({ "outfit_id": outfit_object_id, "user_id": user_object_id })
        return "Sucessfully removed outfit from wishlist"
