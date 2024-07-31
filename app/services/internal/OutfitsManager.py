from bson import ObjectId
from datetime import datetime

class OutfitsManager:
    def __init__(self, mongo_client):
        self.db = mongo_client["drip"]
        self.outfits_collection = self.db["outfits"]
        self.liked_items_collection = self.db["liked_items"]
        self.wishlists_collection = self.db["wishlists"]
        self.closets_collection = self.db["closets"]

    def get_all_outfits(self, page, page_size):
        skip = (page - 1) * page_size
        outfits = list(self.outfits_collection.aggregate([
            {
                "$lookup": {
                    "from": "items",
                    "localField": "items",
                    "foreignField": "_id",
                    "as": "items"
                }
            },
            { "$sort": { "date_created": -1 } },
            { "$skip": skip },
            { "$limit": page_size }
        ]))
        return outfits

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
            },
            { "$sort": { "date_created": -1 } }
        ]))
        return outfits

    def get_outfits_by_item(self, item_id):
        item_object_id = ObjectId(item_id)
        outfits = list(self.outfits_collection.aggregate([
            { "$match": { "items": item_object_id } },
            {
                "$lookup": {
                    "from": "items",
                    "localField": "items",
                    "foreignField": "_id",
                    "as": "items"
                }
            },
            { "$sort": { "date_created": -1 } }
        ]))
        return outfits

    def add_outfit_to_closets(self, outfit_id, closets):
        current_time = datetime.utcnow()
        for closet in closets:
            self.closets_collection.update_one(
                {'_id': ObjectId(closet['_id'])},
                {'$addToSet': {
                    'products': {
                        'type': "outfit", 
                        'id': outfit_id,
                        'date_added': current_time,
                    }
                }}
            )

    def create_outfit(self, user_id, preference, items, media_urls, description, caption, embedding, closets):
        item_ids = [ObjectId(item["_id"]) for item in items]
        user_object_id = ObjectId(user_id)
        current_time = datetime.utcnow()
        result = self.outfits_collection.insert_one({
            "user_id": user_object_id,
            "gender": preference,
            "items": item_ids,
            "images": media_urls,
            "description": description,
            "embedding": embedding,
            "caption": caption,
            "date_created": current_time
        })
        outfit_id = result.inserted_id
        self.add_outfit_to_closets(outfit_id, closets)
        return "Created outfit"    

    def get_liked_outfits(self, user_id):
        user_object_id = ObjectId(user_id)
        liked_outfits = list(self.liked_items_collection.aggregate([
            { "$match": {"liked_by": user_object_id, "post_type": "outfit" } },
            {
                "$lookup": {
                    "from": "outfits",
                    "localField": "post_id",
                    "foreignField": "_id",
                    "as": "outfit"
                }
            },
            { "$unwind": "$outfit" },
            { "$project": { "outfit": 1, "_id": 0 } },
            { "$replaceRoot": { "newRoot": "$outfit" } },
            {
                "$lookup": {
                    "from": "items",
                    "localField": "items",
                    "foreignField": "_id",
                    "as": "items"
                }
            },
            { "$sort": { "date_created": -1 } }
        ]))
        return liked_outfits

    def create_liked_outfit(self, user_id, outfit_id):
        outfit_object_id = ObjectId(outfit_id)
        user_object_id = ObjectId(user_id)
        current_time = datetime.utcnow()

        # Fetch the item to get the user who posted it
        outfit = self.outfits_collection.find_one({"_id": outfit_object_id})
        if not outfit:
            return "Outfit not found"

        posted_by_user_id = outfit["user_id"]

        result = self.liked_items_collection.update_one(
            { "post_id": outfit_object_id, "liked_by": user_object_id },
            { "$setOnInsert": {
                "date_liked": current_time,
                "liked_by": user_object_id,
                "posted_by": posted_by_user_id,
                "post_type": "outfit",
                "post_id": outfit_object_id
            }},
            upsert=True
        )
        return "Outfit already liked" if result.matched_count > 0 else "Outfit was liked"

    def delete_liked_outfit(self, user_id, outfit_id):
        outfit_object_id = ObjectId(outfit_id)
        user_object_id = ObjectId(user_id)
        self.liked_items_collection.delete_one({ "post_id": outfit_object_id, "liked_by": user_object_id })
        return "Sucessfully unliked outfit"

    def get_outfit_liked_count(self, outfit_id):
        outfit_object_id = ObjectId(outfit_id)
        liked_count = self.liked_items_collection.count_documents({ "post_id": outfit_object_id })
        return liked_count
    
    def get_outfit_added_count(self, outfit_id):
        outfit_object_id = ObjectId(outfit_id)
        
        pipeline = [
            {"$match": {"name": "All Products"}},
            {"$unwind": "$products"},
            {"$match": {"products.id": outfit_object_id}},
            {"$group": {"_id": None, "count": {"$sum": 1}}}
        ]
        
        result = list(self.wishlists_collection.aggregate(pipeline))
        
        if result:
            return result[0]['count']
        else:
            return 0

    def check_outfit_owned(self, user_id, outfit_id):
        user_object_id = ObjectId(user_id)
        outfit_object_id = ObjectId(outfit_id)
        outfit = self.outfits_collection.find_one({"_id": outfit_object_id, "user_id": user_object_id})
        return outfit is not None