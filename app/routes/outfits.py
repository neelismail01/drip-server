import json
from flask import (
    Blueprint,
    current_app,
    request
)
import base64
from datetime import datetime
from app.utils.MongoJsonEncoder import MongoJSONEncoder

outfits_blueprint = Blueprint('outfits', __name__)

@outfits_blueprint.route("/", methods=["GET"])
def get_all_outfits():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 5))
    all_outfits = current_app.outfits_manager.get_all_outfits(page, page_size)
    return json.dumps(all_outfits, cls=MongoJSONEncoder)


@outfits_blueprint.route('/<user_id>', methods=["GET"])
def get_outfits(user_id):
    outfits = current_app.outfits_manager.get_outfits_for_user(user_id)
    return json.dumps(outfits, cls=MongoJSONEncoder)

@outfits_blueprint.route('/', methods=["POST"])
def create_outfit():
    data = request.json
    user_id, preference, items, description, caption, pictures = (
        data.get("user_id"),
        data.get("preference"),
        data.get("items"),
        data.get("description"),
        data.get("caption"),
        data.get("media")
    )
    description_embedding = current_app.text_embeddings_manager.get_openai_text_embedding(description)
    media_urls = current_app.cloud_storage_manager.upload_multiple_media_to_gcs(pictures, user_id)
    result = current_app.outfits_manager.create_outfit(
        user_id, preference, items, media_urls, description, caption, description_embedding
    )
    return result, 200

@outfits_blueprint.route('/liked', methods=["GET"])
def get_liked_outfits():
    user_id = request.args.get('user_id')
    outfits = current_app.outfits_manager.get_liked_outfits(user_id)
    return json.dumps(outfits, cls=MongoJSONEncoder)

@outfits_blueprint.route('/liked', methods=["POST"])
def create_liked_outfit():
    data = request.json
    user_id = data.get('user_id')
    outfit = data.get('outfit')
    outfit_id = outfit["_id"]
    result = current_app.outfits_manager.created_liked_outfit(user_id, outfit_id)
    return (result, 200) if result == "Outfit was liked" else (result, 400)

@outfits_blueprint.route('/liked', methods=["DELETE"])
def delete_liked_outfit():
    data = request.json
    user_id = data.get('user_id')
    outfit = data.get('outfit')
    outfit_id = outfit['_id']
    result = current_app.outfits_manager.delete_liked_outfit(user_id, outfit_id)
    return result, 200

@outfits_blueprint.route('/wishlist', methods=["GET"])
def get_wishlist_outfits():
    user_id = request.args.get('user_id')
    outfits = current_app.outfits_manager.get_wishlist_outfits(user_id)
    return json.dumps(outfits, cls=MongoJSONEncoder)

@outfits_blueprint.route('/wishlist', methods=["POST"])
def create_wishlist_outfit():
    data = request.json
    user_id = data.get("user_id")
    outfit = data.get("outfit")
    outfit_id = outfit["_id"]
    result = current_app.outfits_manager.create_wishlist_outfit(user_id, outfit_id)
    return (result, 200) if result == "Outfit added to wishlist" else (result, 400)

@outfits_blueprint.route('/wishlist', methods=["DELETE"])
def delete_wishlist_outfit():
    data = request.json
    user_id = data.get('user_id')
    outfit = data.get('outfit')
    outfit_id = outfit['_id']
    result = current_app.outfits_manager.delete_wishlist_outfit(user_id, outfit_id)
    return result, 200

@outfits_blueprint.route("/liked-count/<outfit_id>", methods=["GET"])
def get_outfit_liked_count(outfit_id):
    liked_count = current_app.outfits_manager.get_outfit_liked_count(outfit_id)
    return json.dumps(liked_count, cls=MongoJSONEncoder)

@outfits_blueprint.route("/added-count/<outfit_id>", methods=["GET"])
def get_outfit_added_count(outfit_id):
    added_count = current_app.outfits_manager.get_outfit_added_count(outfit_id)
    return json.dumps(added_count, cls=MongoJSONEncoder)
