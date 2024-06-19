from bson import ObjectId
from datetime import datetime
from app.utils.constants import DEFAULT_PROFILE_PICTURE

class UserManager:
    def __init__(self, mongo_client):
        self.db = mongo_client["drip"]
        self.users_collection = self.db["users"]

    def get_user_by_email(self, email):
        user = self.users_collection.find_one({ "email": email })
        return user

    def get_user_by_id(self, user_id):
        user_object_id = ObjectId(user_id)
        user = self.users_collection.find_one({ "_id": user_object_id })
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
        return "Updated user"

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