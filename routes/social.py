from flask import (
    current_app,
    Blueprint,
    jsonify,
    request
)
import json

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
