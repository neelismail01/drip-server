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

@outfits_blueprint.route('/<user_id>', methods=["GET"])
def get_outfits(user_id):
    outfits = current_app.outfits_manager.get_outfits_for_user(user_id)
    return json.dumps(outfits, cls=MongoJSONEncoder)

@outfits_blueprint.route('/', methods=["POST"])
def create_outfit():
    data = request.json
    user_id, preference, items, description, caption, media_urls = (
        data.get("user_id"),
        data.get("preference"),
        data.get("items"),
        data.get("description"),
        data.get("caption"),
        data.get("mediaUrls")
    )
    description_embedding = current_app.text_embeddings_manager.get_openai_text_embedding(description)
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
