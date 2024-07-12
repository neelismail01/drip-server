import json
from flask import (
    Blueprint,
    current_app,
    request
)
from app.utils.MongoJsonEncoder import MongoJSONEncoder
from app.utils.constants import DEFAULT_BRAND_LOGO

items_blueprint = Blueprint("items", __name__)

@items_blueprint.route("/", methods=["GET"])
def get_all_items():
    all_items = current_app.items_manager.get_all_items()
    return json.dumps(all_items, cls=MongoJSONEncoder)

@items_blueprint.route("/", methods=["POST"])
def create_item():
    data = request.json
    user_id, preference, caption, description, product_page_link, brand_info, media_urls = (
        data.get("user_id"),
        data.get("preference"),
        data.get("caption"),
        data.get("description"),
        data.get("productPageLink"),
        data.get("brandInfo"),
        data.get("mediaUrls"),
    )
    description_embedding = current_app.text_embeddings_manager.get_openai_text_embedding(description)
    user_info = { "user_id": user_id, "preference": preference }
    item_info = { 
        "caption": caption, 
        "description": description,
        "embedding": description_embedding,
        "media_urls": media_urls, 
        "product_page_link": product_page_link
    }
    brand_info["domain"] = (
        brand_info["domain"] or 
        current_app.custom_search_manager.get_brand_website_domain(brand_info["name"])
    )
    brand_info["icon"] = brand_info["icon"] or DEFAULT_BRAND_LOGO
    result = current_app.items_manager.create_item(user_info, item_info, brand_info)
    return (result, 200) if result == "Item was created" else (result, 400)

@items_blueprint.route("/<user_id>", methods=["GET"])
def get_user_items(user_id):
    user_items = current_app.items_manager.get_user_items(user_id)
    return json.dumps(user_items, cls=MongoJSONEncoder)

@items_blueprint.route("/liked", methods=["GET"])
def get_liked_items():
    user_id = request.args.get("user_id")
    liked_items = current_app.items_manager.get_liked_items(user_id)
    return json.dumps(liked_items, cls=MongoJSONEncoder)

@items_blueprint.route("/liked", methods=["POST"])
def create_liked_item():
    data = request.json
    item_id = data.get("itemId")
    user_id = data.get("user_id")
    result = current_app.items_manager.create_liked_item(item_id, user_id)
    return (result, 200) if result == "Item was liked" else (result, 400)

@items_blueprint.route("/liked", methods=["DELETE"])
def delete_liked_item():
    data = request.json
    item_id = data.get("itemId")
    user_id = data.get("user_id")
    result = current_app.items_manager.delete_liked_item(item_id, user_id)
    return result, 200

@items_blueprint.route("/wishlist", methods=["GET"])
def get_wishlist_items():
    user_id = request.args.get("user_id")
    wishlist_items = current_app.items_manager.get_wishlist_items(user_id)
    return json.dumps(wishlist_items, cls=MongoJSONEncoder)

@items_blueprint.route("/wishlist", methods=["POST"])
def create_wishlist_item():
    data = request.json
    item_id = data.get("itemId")
    user_id = data.get("user_id")
    result = current_app.items_manager.create_wishlist_item(item_id, user_id)
    return (result, 200) if result == "Item was added to wishlist" else (result, 400)

@items_blueprint.route("/wishlist", methods=["DELETE"])
def delete_wishlist_item():
    data = request.json
    item_id = data.get("itemId")
    user_id = data.get("user_id")
    result = current_app.items_manager.delete_wishlist_item(item_id, user_id)
    return result, 200

@items_blueprint.route("/similar", methods=["GET"])
def get_similar_items():
    db = current_app.mongo.drip
    collection = db["items"]
    tag = request.args.get("tag")
    items = collection.find({"tag": tag})
    items_list = list(items)
    return json.dumps(items_list, cls=MongoJSONEncoder)

@items_blueprint.route("/image/analyze", methods=["POST"])
def analyze_item_image():
    data = request.json
    base64_image = data.get("base64_image")
    item_details = current_app.image_vision_manager.get_details_from_item_image(base64_image)
    return json.dumps(item_details, cls=MongoJSONEncoder)

@items_blueprint.route("/liked-count/<item_id>", methods=["GET"])
def get_item_liked_count(item_id):
    liked_count = current_app.items_manager.get_item_liked_count(item_id)
    return json.dumps(liked_count, cls=MongoJSONEncoder)

@items_blueprint.route("/added-count/<item_id>", methods=["GET"])
def get_item_added_count(item_id):
    added_count = current_app.items_manager.get_item_added_count(item_id)
    return json.dumps(added_count, cls=MongoJSONEncoder)

@items_blueprint.route("/owned", methods=["GET"])
def check_item_owned():
    user_id = request.args.get("user_id")
    item_id = request.args.get("item_id")
    owned = current_app.items_manager.check_item_owned(user_id, item_id)
    return json.dumps({"owned": owned}), 200