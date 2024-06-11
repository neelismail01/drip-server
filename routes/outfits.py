import json
from flask import (
    Blueprint,
    current_app,
    request
)
import base64
from datetime import datetime
from services.OutfitsManager import OutfitsManager
from services.CloudStorageManager import cloud_storage_manager
from utils.MongoJsonEncoder import MongoJSONEncoder

outfits_blueprint = Blueprint('outfits', __name__)

@outfits_blueprint.route('/<user_id>', methods=["GET"])
def get_outfits(user_id):
    outfits_manager = OutfitsManager(current_app.mongo)
    outfits = outfits_manager.get_outfits_for_user(user_id)
    return json.dumps(outfits, cls=MongoJSONEncoder)

@outfits_blueprint.route('/', methods=["POST"])
def create_outfit():
    outfits_manager = OutfitsManager(current_app.mongo)
    data = request.json
    user_id = data.get('user_id')
    items = data.get('items')
    description = data.get('description')
    caption = data.get('caption')
    pictures = data.get('pictures')

    media_urls = []
    for media in pictures:
        if media["type"] == "image":
            image_bytes = base64.b64decode(media["data"])
            destination = "outfit_{}_{}".format(user_id, str(datetime.now()))
            gcs_media_url = cloud_storage_manager.upload_media_to_gcs(image_bytes, destination, 'image/jpeg')
            media_urls.append(gcs_media_url)
        else:
            print("Unsupported media format")
    result = outfits_manager.create_outfit(user_id, items, media_urls, description, caption, tags)
    return result, 200

@outfits_blueprint.route('/liked', methods=["GET"])
def get_liked_outfits():
    outfits_manager = OutfitsManager(current_app.mongo)
    user_id = request.args.get('user_id')
    outfits = outfits_manager.get_liked_outfits(user_id)
    return json.dumps(outfits, cls=MongoJSONEncoder)

@outfits_blueprint.route('/liked', methods=["POST"])
def create_liked_outfit():
    outfits_manager = OutfitsManager(current_app.mongo)
    data = request.json
    user_id = data.get('user_id')
    outfit = data.get('outfit')
    outfit_id = outfit["_id"]
    result = outfits_manager.created_liked_outfit(user_id, outfit_id)
    return (result, 200) if result == "Outfit was liked" else (result, 400)

@outfits_blueprint.route('/liked', methods=["DELETE"])
def delete_liked_outfit():
    outfits_manager = OutfitsManager(current_app.mongo)
    data = request.json
    user_id = data.get('user_id')
    outfit = data.get('outfit')
    outfit_id = outfit['_id']
    result = outfits_manager.delete_liked_outfit(user_id, outfit_id)
    return result, 200

@outfits_blueprint.route('/wishlist', methods=["GET"])
def get_wishlist_outfits():
    outfits_manager = OutfitsManager(current_app.mongo)
    user_id = request.args.get('user_id')
    outfits = outfits_manager.get_wishlist_outfits(user_id)
    return json.dumps(outfits, cls=MongoJSONEncoder)

@outfits_blueprint.route('/wishlist', methods=["POST"])
def create_wishlist_outfit():
    outfits_manager = OutfitsManager(current_app.mongo)
    data = request.json
    user_id = data.get("user_id")
    outfit = data.get("outfit")
    outfit_id = outfit["_id"]
    result = outfits_manager.create_wishlist_outfit(user_id, outfit_id)
    return (result, 200) if result == "Outfit added to wishlist" else (result, 400)

@outfits_blueprint.route('/wishlist', methods=["DELETE"])
def delete_wishlist_outfit():
    outfits_manager = OutfitsManager(current_app.mongo)
    data = request.json
    user_id = data.get('user_id')
    outfit = data.get('outfit')
    outfit_id = outfit['_id']
    result = outfits_manager.delete_wishlist_outfit(user_id, outfit_id)
    return result, 200
