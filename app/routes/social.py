from flask import (
    current_app,
    Blueprint,
    request
)
from bson import json_util
from app.utils.MongoJsonEncoder import MongoJSONEncoder

social_blueprint = Blueprint('social', __name__)

@social_blueprint.route('/follow', methods=["POST"])
def follow_user():
    data = request.json
    follower_info = { 
        "id": data.get("follower_id"), 
        "name": data.get("follower_name"), 
        "username": data.get("follower_username")
    }
    followee_info = { 
        "id": data.get("followee_id"), 
        "name": data.get("followee_name"), 
        "username": data.get("followee_username")
    }
    result = current_app.social_network_manager.follow_user(follower_info, followee_info)
    return result, 200

@social_blueprint.route('/unfollow', methods=["POST"])
def unfollow_user():
    data = request.json
    follower_id = data.get("follower_id")
    followee_id = data.get("followee_id")
    result = current_app.social_network_manager.unfollow_user(follower_id, followee_id)
    return result, 200

@social_blueprint.route('/', methods=["GET"])
def check_following_relationship():
    follower_id = request.args.get("follower_id")
    followee_id = request.args.get("followee_id")
    result = current_app.social_network_manager.get_following_relationship(follower_id, followee_id)
    return json_util.dumps(result, cls=MongoJSONEncoder)
    
@social_blueprint.route('/stats/<user_id>', methods=["GET"])
def get_follower_following_stats(user_id):
    all_followers = current_app.social_network_manager.get_all_followers(user_id)
    all_following = current_app.social_network_manager.get_all_following(user_id)
    following_dict = { follow["followee_id"]: follow for follow in all_following }

    following_list = [
        {
            "id": follow["followee_id"],
            "name": follow["followee_name"],
            "username": follow["followee_username"],
            "is_following": True
        }
        for follow in all_following
    ]

    followers_list = [
        {
            "id": follow["follower_id"],
            "name": follow["follower_name"],
            "username": follow["follower_username"],
            "is_following": follow["follower_id"] in following_dict
        }
        for follow in all_followers
    ]
    
    return json_util.dumps({ "following": following_list, "followers": followers_list }, cls=MongoJSONEncoder)