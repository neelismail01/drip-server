from bson import ObjectId
from datetime import datetime
from app.utils.constants import DEFAULT_PROFILE_PICTURE

class UserManager:
    def __init__(self, mongo_client):
        self.db = mongo_client["drip"]
        self.users_collection = self.db["users"]
        self.items_collection = self.db["items"]
        self.outfits_collection = self.db["outfits"]
        self.brands_collection = self.db["brands"]
        self.liked_items_collection = self.db["liked_items"]
        self.wishlists_collection = self.db["wishlists"]

    def get_user_by_email(self, email):
        user = self.users_collection.find_one({ "email": email })
        return user

    def get_user_by_id(self, user_id):
        user_object_id = ObjectId(user_id)
        user = self.users_collection.find_one({ "_id": user_object_id })
        user['_id'] = str(user['_id'])
        return user

    def create_user(self, email, name):
        current_time = datetime.utcnow()
        result = self.users_collection.insert_one({
            "email": email,
            "name": name,
            "profile_complete": False,
            "date_created": current_time,
            "profile_picture": DEFAULT_PROFILE_PICTURE,
            "username": None,
            "preference": None,
            "birthdate": None
        })
        user_id = result.inserted_id
        inserted_user = self.users_collection.find_one({"_id": user_id})

        # create empty "All Products" wishlist for user
        self.wishlists_collection.insert_one({
            'date_created': current_time,
            'name': "All Products",
            'user_id': user_id,
            'products': [],
        })

        return inserted_user

    def check_username_exists(self, username):
        user = self.users_collection.find_one({ "username": username })
        return user

    def complete_user_onboarding(self, user_id, username, preference, birthdate):
        user_object_id = ObjectId(user_id)
        date_object = datetime.strptime(birthdate, '%Y-%m-%d')
        self.users_collection.update_one(
            { "_id": user_object_id },
            { "$set": { "username": username, "preference": preference, "birthdate": date_object, "profile_complete": True } }
        )
        updated_user = self.users_collection.find_one({"_id": user_object_id})
        return updated_user

    def get_profile_picture(self, user_id):
        user_object_id = ObjectId(user_id)
        user = self.users_collection.find_one({ "_id": user_object_id })
        return user["profile_picture"]

    def update_profile_picture(self, user_id, profile_picture):
        user_object_id = ObjectId(user_id)
        self.users_collection.update_one(
            { "_id": user_object_id },
            { "$set": { "profile_picture": profile_picture } }
        )

    def get_most_shopped_brands(self, user_id):
        pipeline = [
            {"$match": {"user_id": ObjectId(user_id)}},
            {"$group": {"_id": "$brand", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]

        most_shopped_brands = list(self.items_collection.aggregate(pipeline))

        top_brands = []
        for brand in most_shopped_brands:
            full_brand = self.brands_collection.find_one({"name": brand['_id']})
            full_brand['count'] = brand['count']
            full_brand['_id'] = str(full_brand['_id'])
            top_brands.append(full_brand)

        return top_brands

    def get_user_liked_count(self, user_id):
        user_object_id = ObjectId(user_id)
        liked_count = self.liked_items_collection.count_documents({ "posted_by": user_object_id })
        return liked_count

    def get_user_post_count(self, user_id):
        user_object_id = ObjectId(user_id)
        item_count = self.items_collection.count_documents({ "user_id": user_object_id })
        outfit_count = self.outfits_collection.count_documents({ "user_id": user_object_id })
        post_count = item_count + outfit_count
        return post_count

    def get_user_added_count(self, user_id):
        user_object_id = ObjectId(user_id)
        
        pipeline = [
            {"$match": {"name": "All Products"}},
            {"$unwind": "$products"},
            {"$match": {"products.posted_by": user_object_id}},
            {"$group": {"_id": None, "count": {"$sum": 1}}}
        ]
        
        result = list(self.wishlists_collection.aggregate(pipeline))
        
        if result:
            return result[0]['count']
        else:
            return 0
