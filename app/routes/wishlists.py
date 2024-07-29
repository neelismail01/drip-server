import json
from flask import (
    Blueprint,
    current_app,
    request
)
from app.utils.MongoJsonEncoder import MongoJSONEncoder

wishlists_blueprint = Blueprint("wishlists", __name__)

@wishlists_blueprint.route("/", methods=["POST"])
def create_wishlist():
    data = request.json
    name = data.get("name")
    user_id = data.get("user_id")
    result = current_app.wishlists_manager.create_wishlist(name, user_id)
    return result

@wishlists_blueprint.route("/", methods=["DELETE"])
def delete_wishlist():
    data = request.json
    name = data.get("name")
    user_id = data.get("user_id")
    result = current_app.wishlists_manager.delete_wishlist(name, user_id)
    return result

@wishlists_blueprint.route("/<user_id>", methods=["GET"])
def get_wishlists_by_user(user_id):
    wishlists = current_app.wishlists_manager.get_wishlists_by_user(user_id)
    return json.dumps(wishlists, cls=MongoJSONEncoder)

@wishlists_blueprint.route("/products", methods=["GET"])
def get_products_by_wishlist():
    user_id = request.args.get("user_id")
    wishlist = request.args.get("wishlist")
    products = current_app.wishlists_manager.get_products_by_wishlist(user_id, wishlist)
    return json.dumps(products, cls=MongoJSONEncoder)

@wishlists_blueprint.route("/<product_id>/<product_type>", methods=["POST"])
def edit_wishlist_memberships(product_id, product_type):
    data = request.json
    wishlists = data.get("wishlists")
    user_id = data.get("user_id")
    result = current_app.wishlists_manager.edit_wishlist_memberships(wishlists, user_id, product_id, product_type)
    return result