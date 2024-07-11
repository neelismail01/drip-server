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

    def insert_new_brand(self, brand_info, user_id):
        user = self.users_collection.find_one({'_id': user_id})
        existing_brand = self.brands_collection.find_one({'name': brand_info["name"]})
        current_time = datetime.utcnow()
        if not existing_brand:
            new_brand = self.brands_collection.insert_one({
                'date_created': current_time,
                'name': brand_info["name"],
                'domain': brand_info["domain"],
                'profile_picture': brand_info["icon"],
            })
            self.social_collection.insert_one({
                "follower_id": user['_id'],
                "follower_name": user["name"],
                "follower_username": user["username"],
                "follower_account_type": "user",
                "followee_id": new_brand.inserted_id,
                "followee_name": brand_info["name"],
                "followee_username": brand_info["domain"],
                "followee_account_type": "brand",
                "status": "SUCCESSFUL",
                "date_created": current_time
            })
        else:
            follow_exists = self.social_collection.find_one({
                "follower_id": user['_id'],
                "followee_id": existing_brand['_id']
            })
            if not follow_exists:
                self.social_collection.insert_one({
                    "follower_id": user['_id'],
                    "follower_name": user["name"],
                    "follower_username": user["username"],
                    "follower_account_type": "user",
                    "followee_id": existing_brand['_id'],
                    "followee_name": existing_brand["name"],
                    "followee_username": existing_brand["domain"],
                    "followee_account_type": "brand",
                    "status": "SUCCESSFUL",
                    "date_created": current_time
                })

    def create_item(self, user_info, item_info, brand_info):
        user_object_id = ObjectId(user_info["user_id"])
        self.insert_new_brand(brand_info, user_object_id)
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
        user_items = list(self.items_collection.find({'user_id': user_object_id}).sort("date_created", -1))
        return user_items

    def get_liked_items(self, user_id):
        user_object_id = ObjectId(user_id)
        liked_items = list(self.liked_items_collection.aggregate([
            { "$match": { "liked_by": user_object_id, "post_type": "item" } },
            {
                "$lookup": {
                    "from": "items",
                    "localField": "post_id",
                    "foreignField": "_id",
                    "as": "item"
                }
            },
            { "$unwind": "$item" },
            { "$project": { "item": 1, "_id": 0 } },
            { "$replaceRoot": { "newRoot": "$item" } },
            { "$sort": { "date_created": -1 } }
        ]))
        return liked_items

    def create_liked_item(self, item_id, user_id):
        item_object_id = ObjectId(item_id)
        user_object_id = ObjectId(user_id)
        current_time = datetime.utcnow()

        # Fetch the item to get the user who posted it
        item = self.items_collection.find_one({"_id": item_object_id})
        if not item:
            return "Item not found"

        posted_by_user_id = item["user_id"]

        result = self.liked_items_collection.update_one(
            { "post_id": item_object_id, "liked_by": user_object_id },
            { "$setOnInsert": {
                "date_liked": current_time,
                "liked_by": user_object_id,
                "posted_by": posted_by_user_id,
                "post_type": "item",
                "post_id": item_object_id
            }},
            upsert=True
        )
        return "Item already liked" if result.matched_count > 0 else "Item was liked"

    def delete_liked_item(self, item_id, user_id):
        item_object_id = ObjectId(item_id)
        user_object_id = ObjectId(user_id)
        self.liked_items_collection.delete_one({ "post_id": item_object_id, "liked_by": user_object_id })
        return "Sucessfully unliked item"

    def get_wishlist_items(self, user_id):
        user_object_id = ObjectId(user_id)
        wishlist_items = list(self.wishlist_items_collection.aggregate([
            { "$match": { "added_by": user_object_id, "post_type": "item" } },
            {
                "$lookup": {
                    "from": "items",
                    "localField": "post_id",
                    "foreignField": "_id",
                    "as": "item"
                }
            },
            { "$unwind": "$item" },
            { "$project": { "item": 1, "_id": 0 } },
            { "$replaceRoot": { "newRoot": "$item" } },
            { "$sort": { "date_created": -1 } }
        ]))
        return wishlist_items

    def create_wishlist_item(self, item_id, user_id):
        item_object_id = ObjectId(item_id)
        user_object_id = ObjectId(user_id)
        current_time = datetime.utcnow()

        # Fetch the item to get the user who posted it
        item = self.items_collection.find_one({"_id": item_object_id})
        if not item:
            return "Item not found"

        posted_by_user_id = item["user_id"]

        result = self.wishlist_items_collection.update_one(
            { "post_id": item_object_id, "added_by": user_object_id },
            { "$setOnInsert": {
                "date_liked": current_time,
                "added_by": user_object_id,
                "posted_by": posted_by_user_id,
                "post_type": "item",
                "post_id": item_object_id
            }},
            upsert=True
        )
        return "Item already in wishlist" if result.matched_count > 0 else "Item was added to wishlist"

    def delete_wishlist_item(self, item_id, user_id):
        item_object_id = ObjectId(item_id)
        user_object_id = ObjectId(user_id)
        self.wishlist_items_collection.delete_one({ "post_id": item_object_id, "added_by": user_object_id })
        return "Sucessfully removed item from wishlist"

    def get_item_liked_count(self, item_id):
        item_object_id = ObjectId(item_id)
        liked_count = self.liked_items_collection.count_documents({ "post_id": item_object_id })
        return liked_count
    
    def get_item_added_count(self, item_id):
        item_object_id = ObjectId(item_id)
        added_count = self.wishlist_items_collection.count_documents({ "post_id": item_object_id })
        return added_count
        
    def check_item_owned(self, user_id, item_id):
        user_object_id = ObjectId(user_id)
        item_object_id = ObjectId(item_id)
        item = self.items_collection.find_one({"_id": item_object_id, "user_id": user_object_id})
        return item is not None

    def get_user_liked_count(self, user_id):
        user_object_id = ObjectId(user_id)
        liked_count = self.liked_items_collection.count_documents({ "posted_by": user_object_id })
        return liked_count