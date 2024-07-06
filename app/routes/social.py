from flask import (
    current_app,
    Blueprint,
    request
)
from bson import json_util
from app.utils.MongoJsonEncoder import MongoJSONEncoder

social_blueprint = Blueprint('social', __name__)

@social_blueprint.route('/follow', methods=["POST"])
def follow_account():
    data = request.json
    follower_info = { 
        "id": data.get("follower_id"), 
        "name": data.get("follower_name"), 
        "username": data.get("follower_username"),
        "account_type": data.get("follower_account_type")
    }
    followee_info = { 
        "id": data.get("followee_id"), 
        "name": data.get("followee_name"), 
        "username": data.get("followee_username"),
        "account_type": data.get("followee_account_type")
    }
    result = current_app.social_network_manager.follow_account(follower_info, followee_info)
    return result, 200

@social_blueprint.route('/unfollow', methods=["POST"])
def unfollow_account():
    data = request.json
    follower_id, followee_id = data.get("follower_id"), data.get("followee_id")
    result = current_app.social_network_manager.unfollow_account(follower_id, followee_id)
    return result, 200

@social_blueprint.route('/', methods=["GET"])
def check_following_relationship():
    follower_id = request.args.get("follower_id")
    followee_id = request.args.get("followee_id")
    result = current_app.social_network_manager.get_following_relationship(follower_id, followee_id)
    return json_util.dumps(result, cls=MongoJSONEncoder)

@social_blueprint.route('/followers/<user_id>/count', methods=["GET"])
def get_followers_count(user_id):
    followers_count = current_app.social_network_manager.get_follower_count(user_id)
    return json_util.dumps(followers_count, cls=MongoJSONEncoder)

@social_blueprint.route('/following/<user_id>/count', methods=["GET"])
def get_following_count(user_id):
    following_count = current_app.social_network_manager.get_following_count(user_id)
    return json_util.dumps(following_count, cls=MongoJSONEncoder)

@social_blueprint.route('/followers/<user_id>', methods=["GET"])
def get_followers(user_id):
    followers = current_app.social_network_manager.get_all_followers(user_id)
    return json_util.dumps(followers, cls=MongoJSONEncoder)

@social_blueprint.route('/following/<user_id>', methods=["GET"])
def get_following(user_id):
    following = current_app.social_network_manager.get_all_following(user_id)
    return json_util.dumps(following, cls=MongoJSONEncoder)

    
@social_blueprint.route('/followers/mutual', methods=["POST"])
def get_mutal_followers():
    data = request.json
    user_id, visited_account_id = data.get("userId"), data.get("visitedAccountId")
    mutual_followers = current_app.social_network_manager.get_mutual_followers(user_id, visited_account_id)
    return json_util.dumps(mutual_followers, cls=MongoJSONEncoder)
