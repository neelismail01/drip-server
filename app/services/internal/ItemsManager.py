from bson import ObjectId
from datetime import datetime

class ItemsManager:
    def __init__(self, mongo_client):
        self.db = mongo_client["drip"]
        self.users_collection = self.db["users"]
        self.items_collection = self.db["items"]
        self.liked_items_collection = self.db["liked_items"]
        self.wishlist_items_collection = self.db["wishlist_items"]
        self.brands_collection = self.db['brands']
        self.social_collection = self.db["social_graph"]

    def get_all_items(self):
        items = list(self.items_collection.find({}))
        return items

    def insert_new_brand(self, brand_info):
        existing_brand = self.brands_collection.find_one({'brand_name': brand_info["name"]})
        if not existing_brand:
            current_time = datetime.utcnow()
            self.brands_collection.insert_one({
                'date_created': current_time,
                'name': brand_info["name"],
                'username': None,
                'domain': brand_info["domain"],
                'profile_picture': brand_info["icon"],
            })

    def create_item(self, user_info, item_info, brand_info):
        user_object_id = ObjectId(user_info["user_id"])
        self.insert_new_brand(brand_info)
        current_time = datetime.utcnow()
        result = self.items_collection.insert_one({
            "user_id": user_object_id,
            "gender": user_info["preference"],
            "brand": brand_info["name"],
            "description": item_info["description"],
            "embedding": item_info["embedding"],
            "caption": item_info["caption"],
            "images": item_info["media_urls"],
            "product_page_link": item_info["product_page_link"] or brand_info["domain"],
            "date_created": current_time
        })
        return "Item was created" if result else "Error creating item"

    def get_user_items(self, user_id):
        user_object_id = ObjectId(user_id)
        user_items = list(self.items_collection.find({'user_id': user_object_id}))
        return user_items

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

    def get_item_liked_count(self, item_id):
        item_object_id = ObjectId(item_id)
        liked_count = self.liked_items_collection.count_documents({ "item_id": item_object_id })
        return liked_count
    
    def get_item_added_count(self, item_id):
        item_object_id = ObjectId(item_id)
        added_count = self.wishlist_items_collection.count_documents({ "item_id": item_object_id })
        return added_count