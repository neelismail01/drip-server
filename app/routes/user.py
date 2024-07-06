import json
from flask import (
    current_app,
    Blueprint,
    request
)
from bson import json_util, ObjectId
from app.utils.MongoJsonEncoder import MongoJSONEncoder

user_blueprint = Blueprint("user", __name__)

@user_blueprint.route("/signin", methods=["POST"])
def signin_user():
    data = request.json
    email = data.get("email")
    user = current_app.user_manager.get_user_by_email(email)
    if not user:
        name = data.get("name")
        user = current_app.user_manager.create_user(email, name)
    return json.dumps(user, cls=MongoJSONEncoder)

@user_blueprint.route("/signup", methods=["PUT"])
def complete_user_profile_creation():
    data = request.json
    user_id = data.get("user_id")
    username = data.get("username")
    preference = data.get("preference")
    birthdate = data.get("birthdate")
    updated_user = current_app.user_manager.complete_user_onboarding(user_id, username, preference, birthdate)
    return json.dumps(updated_user, cls=MongoJSONEncoder), 200

@user_blueprint.route("/username", methods=["GET"])
def check_username_exists():
    username = request.args.get("username")
    user = current_app.user_manager.check_username_exists(username)
    return json_util.dumps(user, cls=MongoJSONEncoder)

@user_blueprint.route("/<user_id>", methods=["GET"])
def get_user(user_id):
    user = current_app.user_manager.get_user_by_id(user_id)
    return json_util.dumps(user, cls=MongoJSONEncoder)
        
@user_blueprint.route("/profile_picture/<user_id>", methods=["GET"])
def get_user_profile_pic(user_id):
    profile_picture = current_app.user_manager.get_profile_picture(user_id)
    return json_util.dumps(profile_picture, cls=MongoJSONEncoder)

@user_blueprint.route("/profile_picture", methods=["PUT"])
def update_profile_picture():
    data = request.json
    user_id, media_url = data.get("user_id"), data.get("media_url")
    current_app.user_manager.update_profile_picture(user_id, media_url)
    return json_util.dumps(media_url, cls=MongoJSONEncoder)

@user_blueprint.route("/top_brands/<user_id>", methods=["GET"])
def get_most_shopped_brands(user_id):
    top_brands = current_app.user_manager.get_most_shopped_brands(user_id)
    return json_util.dumps(top_brands, cls=MongoJSONEncoder)

@user_blueprint.route("/brands_following/<user_id>/<my_user_id>", methods=["GET"])
def get_brands_following(user_id, my_user_id):
    db = current_app.mongo.drip
    brands_collection = db["brands"]
    followed_brands_cursor = brands_collection.find({"followers": ObjectId(user_id)})
    followed_brands = []
    for brand in followed_brands_cursor:
        brand["_id"] = str(brand["_id"])
        is_following_brand = False
        for follower in brand["followers"]:
            if str(follower) == my_user_id:
                is_following_brand = True
        brand["is_following_brand"] = is_following_brand
        followed_brands.append(brand)
    return json_util.dumps(followed_brands, cls=MongoJSONEncoder)
