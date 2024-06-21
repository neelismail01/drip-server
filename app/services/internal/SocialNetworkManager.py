from bson import ObjectId
from datetime import datetime

class SocialNetworkManager:
    def __init__(self, mongo_client):
        self.db = mongo_client["drip"]
        self.social_collection = self.db["social_graph"]
        self.users_collection = self.db["users"]
        self.brands_collection = self.db["brands"]

    def follow_user(self, follower_info, followee_info):
        current_time = datetime.utcnow()
        self.social_collection.insert_one({
            "follower_id": ObjectId(follower_info["id"]),
            "follower_name": follower_info["name"],
            "follower_username": follower_info["username"],
            "follower_profilePicture": follower_info['profilePicture'],
            "followee_id": ObjectId(followee_info["id"]),
            "followee_name": followee_info["name"],
            "followee_username": followee_info["username"],
            "followee_profilePicture": followee_info['profilePicture'],
            "status": "SUCCESSFUL",
            "date_created": current_time
        })
        return "Successfully followed user"

    def unfollow_user(self, follower_id, followee_id):
        follower_object_id = ObjectId(follower_id)
        followee_object_id = ObjectId(followee_id)
        self.social_collection.delete_one({ "follower_id": follower_object_id, "followee_id": followee_object_id })
        return "Successfully unfollowed user"

    def get_following_relationship(self, follower_id, followee_id):
        follower_object_id = ObjectId(follower_id)
        followee_object_id = ObjectId(followee_id)
        result = self.social_collection.find_one({ "follower_id": follower_object_id, "followee_id": followee_object_id })
        return result

    def get_follower_count(self, user_id):
        user_object_id = ObjectId(user_id)
        follower_count = self.social_collection.count_documents({ "followee_id": user_object_id, "status": "SUCCESSFUL" })
        return follower_count

    def get_following_count(self, user_id):
        user_object_id = ObjectId(user_id)
        following_count = self.social_collection.count_documents({ "follower_id": user_object_id, "status": "SUCCESSFUL" })
        return following_count

    def get_all_followers(self, user_id):
        user_object_id = ObjectId(user_id)
        followers = list(self.social_collection.find({ "followee_id": user_object_id, "status": "SUCCESSFUL" }))
        return followers

    def get_all_following(self, user_id):
        user_object_id = ObjectId(user_id)
        followings = list(self.social_collection.find({ "follower_id": user_object_id, "status": "SUCCESSFUL" }))
        return followings


