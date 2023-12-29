from flask import (
    current_app,
    Blueprint,
    jsonify,
    request
)
from bson import json_util

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