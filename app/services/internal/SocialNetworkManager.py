from bson import ObjectId
from datetime import datetime

class SocialNetworkManager:
    def __init__(self, mongo_client):
        self.db = mongo_client["drip"]
        self.social_collection = self.db["social_graph"]
        self.users_collection = self.db["users"]
        self.brands_collection = self.db["brands"]

    def follow_account(self, follower_info, followee_info):
        current_time = datetime.utcnow()
        self.social_collection.insert_one({
            "follower_id": ObjectId(follower_info["id"]),
            "follower_name": follower_info["name"],
            "follower_username": follower_info["username"],
            "follower_account_type": follower_info['account_type'],
            "followee_id": ObjectId(followee_info["id"]),
            "followee_name": followee_info["name"],
            "followee_username": followee_info["username"],
            "followee_account_type": followee_info['account_type'],
            "status": "SUCCESSFUL",
            "date_created": current_time
        })
        return "Successfully followed user"

    def unfollow_account(self, follower_id, followee_id):
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

    def get_mutual_followers(self, user_id, visited_account_id):
        user_object_id = ObjectId(user_id)
        visited_account_object_id = ObjectId(visited_account_id)
        mutual_followers = list(self.social_collection.aggregate([
            # Match documents where the followee is either user1 or user2
            {'$match': {
                'followee_id': {'$in': [user_object_id, visited_account_object_id]}
            }},
            # Group by follower_id and count the number of documents
            {'$group': {
                '_id': '$follower_id',
                'count': {'$sum': 1}
            }},
            # Filter to keep only followers who follow both users
            {'$match': {
                'count': 2
            }},
            # Look up the user details from the users collection
            {'$lookup': {
                'from': 'users',
                'localField': '_id',
                'foreignField': '_id',
                'as': 'user_details'
            }},
            # Unwind the user_details array
            {'$unwind': '$user_details'},
            # Project only the fields we want
            {'$project': {
                '_id': 1,
                'username': '$user_details.username',
            }}
        ]))
        
        return mutual_followers
