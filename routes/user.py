import json
from flask import (
    current_app,
    Blueprint,
    request
)
import base64
from datetime import datetime
from bson import json_util
from services.UserManager import UserManager
from services.CloudStorageManager import CloudStorageManager
from utils.MongoJsonEncoder import MongoJSONEncoder

user_blueprint = Blueprint("user", __name__)

@user_blueprint.route("/signin", methods=["POST"])
def signin_user():
    user_manager = UserManager(current_app.mongo)
    data = request.json
    email = data.get("email")
    user = user_manager.get_user_by_email(email)
    if not user:
        name = data.get("name")
        user = user_manager.create_user(email, name)
    return json.dumps(user, cls=MongoJSONEncoder)

@user_blueprint.route("/signup", methods=["PUT"])
def complete_user_profile_creation():
    user_manager = UserManager(current_app.mongo)
    data = request.json
    user_id = data.get("user_id")
    username = data.get("username")
    preference = data.get("preference")
    birthdate = data.get("birthdate")
    user_manager.complete_user_onboarding(user_id, username, preference, birthdate)
    return "Successfully updated user"

@user_blueprint.route("/username", methods=["GET"])
def check_username_exists():
    user_manager = UserManager(current_app.mongo)
    username = request.args.get("username")
    user = user_manager.check_username_exists(username)
    return json_util.dumps(user, cls=MongoJSONEncoder)

@user_blueprint.route("/<user_id>", methods=["GET"])
def get_user(user_id):
    user_manager = UserManager(current_app.mongo)
    user = user_manager.get_user_by_id(user_id)
    return json_util.dumps(user, cls=MongoJSONEncoder)
        
@user_blueprint.route("/profile_pic/<user_id>", methods=["GET"])
def get_user_profile_pic(user_id):
    user_manager = UserManager(current_app.mongo)
    profile_picture = user_manager.get_profile_picture(user_id)
    return json_util.dumps(profile_picture, cls=MongoJSONEncoder)

@user_blueprint.route("/profile_picture", methods=["PUT"])
def update_profile_picture():
    user_manager = UserManager(current_app.mongo)
    cloud_storage_manager = CloudStorageManager()

    data = request.json
    user_id = data.get("user_id")
    profile_picture = data.get("profile_pic")

    image_bytes = base64.b64decode(profile_picture)
    destination = "profile_picture_{}_{}.jpg".format(str(user_id), str(datetime.now()))
    media_url = cloud_storage_manager.upload_base64_file("drip-bucket-1", image_bytes, destination)
    user_manager.update_profile_picture(user_id, media_url)
    return json_util.dumps(media_url, cls=MongoJSONEncoder)

@user_blueprint.route("/brands_following/<user_id>/<my_user_id>", methods=["GET"])
def get_brands_following(user_id, my_user_id):
    db = current_app.mongo.drip
    brands_collection = db["brands"]
    followed_brands_cursor = brands_collection.find({"followers": user_id})
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
