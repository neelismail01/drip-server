import json
from flask import (
    Blueprint,
    current_app,
    request
)
from services.ItemsManager import ItemsManager
from utils.MongoJsonEncoder import MongoJSONEncoder

items_blueprint = Blueprint("items", __name__)

@items_blueprint.route("/", methods=["GET"])
def get_all_items():
    items_manager = ItemsManager(current_app.mongo)
    all_items = items_manager.get_all_items()
    return json.dumps(all_items, cls=MongoJSONEncoder)

@items_blueprint.route("/", methods=["POST"])
def create_item():
    items_manager = ItemsManager(current_app.mongo)
    data = request.json
    item = {
        "user_id": data.get('user_id'),
        "brand": data.get('brand'),
        "color": data.get('color'),
        "item_name": data.get('name'),
        "caption": data.get('caption'),
        "images": data.get('pictures'),
        "tags": data.get('tags')
    }
    result = items_manager.create_item(item)
    return (result, 200) if result == "Item was created" else (result, 400)

@items_blueprint.route("/", methods=["GET"])
def get_user_items():
    user_id = request.args.get("user_id")
    items_manager = ItemsManager(current_app.mongo)
    user_items = items_manager.get_user_items(user_id)
    return json.dumps(user_items, cls=MongoJSONEncoder)

@items_blueprint.route("/liked", methods=["GET"])
def get_liked_items():
    items_manager = ItemsManager(current_app.mongo)
    user_id = request.args.get("user_id")
    liked_items = items_manager.get_liked_items(user_id)
    return json.dumps(liked_items, cls=MongoJSONEncoder)

@items_blueprint.route("/liked", methods=["POST"])
def create_liked_item():
    items_manager = ItemsManager(current_app.mongo)
    data = request.json
    item_id = data.get("itemId")
    user_id = data.get("user_id")
    result = items_manager.create_liked_item(item_id, user_id)
    return (result, 200) if result == "Item was liked" else (result, 400)

@items_blueprint.route("/liked", methods=["DELETE"])
def delete_liked_item():
    items_manager = ItemsManager(current_app.mongo)
    data = request.json
    item_id = data.get("itemId")
    user_id = data.get("user_id")
    result = items_manager.delete_liked_item(item_id, user_id)
    return result, 200

@items_blueprint.route("/wishlist", methods=["GET"])
def get_wishlist_items():
    items_manager = ItemsManager(current_app.mongo)
    user_id = request.args.get("user_id")
    wishlist_items = items_manager.get_wishlist_items(user_id)
    return json.dumps(wishlist_items, cls=MongoJSONEncoder)

@items_blueprint.route("/wishlist", methods=["POST"])
def create_wishlist_item():
    items_manager = ItemsManager(current_app.mongo)
    data = request.json
    item_id = data.get("itemId")
    user_id = data.get("user_id")
    result = items_manager.create_wishlist_item(item_id, user_id)
    return (result, 200) if result == "Item was added to wishlist" else (result, 400)

@items_blueprint.route("/wishlist", methods=["DELETE"])
def delete_wishlist_item():
    items_manager = ItemsManager(current_app.mongo)
    data = request.json
    item_id = data.get("itemId")
    user_id = data.get("user_id")
    result = items_manager.delete_wishlist_item(item_id, user_id)
    return result, 200

@items_blueprint.route("/similar", methods=["GET"])
def get_similar_items():
    db = current_app.mongo.drip
    collection = db["items"]
    tag = request.args.get("tag")
    items = collection.find({"tag": tag})
    items_list = list(items)
    return json.dumps(items_list, cls=MongoJSONEncoder)
