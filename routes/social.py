from flask import (
    current_app,
    Blueprint,
    jsonify,
    request
)
from bson import json_util, ObjectId

social_blueprint = Blueprint('social', __name__)

@social_blueprint.route('/follow', methods=["POST"])
def follow_user():
    db = current_app.mongo.drip
    data = request.json
    if request.method == "POST":
        print(data)
        follower_id = data.get("follower_id")
        follower_name = data.get("follower_name")
        follower_username = data.get("follower_username")
        followee_id = data.get("followee_id")
        followee_name = data.get("followee_name")
        followee_username = data.get("followee_username")

        db.social_graph.insert_one({
            "follower_id": follower_id,
            "follower_name": follower_name,
            "follower_username": follower_username,
            "followee_id": followee_id,
            "followee_name": followee_name,
            "followee_username": followee_username,
            "status": "SUCCESSFUL"
        })

        return "Successfully sent follow request", 200

@social_blueprint.route('/unfollow', methods=["POST"])
def unfollow_user():
    db = current_app.mongo.drip
    data = request.json
    if request.method == "POST":
        follower_id = data.get("follower_id")
        followee_id = data.get("followee_id")

        result = db.social_graph.delete_one({
            "follower_id": follower_id,
            "followee_id": followee_id
        })

        if result.deleted_count > 0:
            return "Successfully unfollowed user", 200
        else:
            return "Failed to unfollow user or follow relationship does not exist", 400


@social_blueprint.route('/', methods=["GET"])
def check_following_relationship():
    db = current_app.mongo.drip
    if request.method == "GET":
        follower_id = request.args.get("follower_id")
        followee_id = request.args.get("followee_id")
        relationship = db.social_graph.find_one({
            "follower_id": follower_id,
            "followee_id": followee_id
        })
        return json_util.dumps(relationship), 200
    
@social_blueprint.route('/stats/<user_id>', methods=["GET"])
def get_follower_following_stats(user_id):
    db = current_app.mongo.drip
    if request.method == "GET":
        # Ensure user_id is a valid ObjectId
        try:
            user_object_id = ObjectId(user_id)
        except Exception as e:
            return jsonify({"error": "Invalid user ID"}), 400

        # Query to find users this user follows
        following = db.social_graph.find({
            "follower_id": str(user_object_id),
            "status": "SUCCESSFUL"
        })

        # Query to find users who follow this user
        followers = db.social_graph.find({
            "followee_id": str(user_object_id),
            "status": "SUCCESSFUL"
        })

        # Convert following and followers to lists of user objects
        following_list = []
        followers_list = []

        for follow in following:
            followee_id = follow.get("followee_id")
            following_list.append({
                "id": followee_id,
                "name": follow.get("followee_name"),
                "username": follow.get("followee_username"),
                "is_following": True
            })

        for follow in followers:
            follower_id = follow.get("follower_id")
            is_following = db.social_graph.find_one({
                "follower_id": str(user_object_id),
                "followee_id": follower_id,
                "status": "SUCCESSFUL"
            }) is not None

            followers_list.append({
                "id": follower_id,
                "name": follow.get("follower_name"),
                "username": follow.get("follower_username"),
                "is_following": is_following
            })

        return jsonify({
            "following": following_list,
            "followers": followers_list
        }), 200