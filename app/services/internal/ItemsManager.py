from bson import ObjectId
from datetime import datetime

class ItemsManager:
    def __init__(self, mongo_client):
        self.db = mongo_client["drip"]
        self.users_collection = self.db["users"]
        self.items_collection = self.db["items"]
        self.outfits_collection = self.db["outfits"]
        self.liked_items_collection = self.db["liked_items"]
        self.wishlists_collection = self.db["wishlists"]
        self.brands_collection = self.db['brands']
        self.social_collection = self.db["social_graph"]
        self.closets_collection = self.db["closets"]

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

    def add_item_to_closets(self, item_id, closets):
        current_time = datetime.utcnow()
        for closet in closets:
            self.closets_collection.update_one(
                {'_id': ObjectId(closet['_id'])},
                {'$addToSet': {
                    'products': {
                        'type': "item", 
                        'id': item_id,
                        'date_added': current_time,
                    }
                }}
            )

    def create_item(self, user_info, item_info, brand_info, closets):
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
        item_id = result.inserted_id
        self.add_item_to_closets(item_id, closets)
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

    def get_item_liked_count(self, item_id):
        item_object_id = ObjectId(item_id)
        liked_count = self.liked_items_collection.count_documents({ "post_id": item_object_id })
        return liked_count
    
    def get_item_added_count(self, item_id):
        item_object_id = ObjectId(item_id)
        
        pipeline = [
            {"$match": {"name": "All Products"}},
            {"$unwind": "$products"},
            {"$match": {"products.id": item_object_id}},
            {"$group": {"_id": None, "count": {"$sum": 1}}}
        ]
        
        result = list(self.wishlists_collection.aggregate(pipeline))
        
        if result:
            return result[0]['count']
        else:
            return 0
        
    def check_item_owned(self, user_id, item_id):
        user_object_id = ObjectId(user_id)
        item_object_id = ObjectId(item_id)
        item = self.items_collection.find_one({"_id": item_object_id, "user_id": user_object_id})
        return item is not None

    def delete_outfit_with_item(self, outfit_id):
        outfit_object_id = ObjectId(outfit_id)

        # Delete outfit from outfits collection
        self.outfits_collection.delete_one({'_id': outfit_object_id})

        # Delete outfit from all closets in closets_collection
        self.closets_collection.update_many(
            {'products.id': outfit_object_id, 'products.type': 'outfit'},
            {'$pull': {'products': {'id': outfit_object_id, 'type': 'outfit'}}}
        )

        # Delete outfit from all likes in liked_items_collection
        self.liked_items_collection.delete_many({'post_id': outfit_object_id, 'post_type': 'outfit'})

        # Delete outfit from all wishlists in wishlists_collection
        self.wishlists_collection.update_many(
            {'products.id': outfit_object_id, 'products.type': 'outfit'},
            {'$pull': {'products': {'id': outfit_object_id, 'type': 'outfit'}}}
        )

        return "Outfit and all references deleted successfully"

    def delete_item(self, item_id):
        item_object_id = ObjectId(item_id)

        # Delete item from items collection
        self.items_collection.delete_one({'_id': item_object_id})

        # Delete item from all closets in closets_collection
        self.closets_collection.update_many(
            {'products.id': item_object_id, 'products.type': 'item'},
            {'$pull': {'products': {'id': item_object_id, 'type': 'item'}}}
        )

        # Delete item from all likes in liked_items_collection
        self.liked_items_collection.delete_many({'post_id': item_object_id, 'post_type': 'item'})

        # Delete item from all wishlists in wishlists_collection
        self.wishlists_collection.update_many(
            {'products.id': item_object_id, 'products.type': 'item'},
            {'$pull': {'products': {'id': item_object_id, 'type': 'item'}}}
        )

        # Delete all outfits containing this item in outfits_collection
        outfits_containing_item = self.outfits_collection.find({'items': item_object_id})
        for outfit in outfits_containing_item:
            outfit_id = outfit['_id']
            self.delete_outfit_with_item(outfit_id)

        return "Item and all references deleted successfully"