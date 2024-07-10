import json
from flask import (
    Blueprint,
    current_app,
    request
)
from app.utils.MongoJsonEncoder import MongoJSONEncoder

closets_blueprint = Blueprint("closets", __name__)

@closets_blueprint.route("/", methods=["POST"])
def create_closet():
    data = request.json
    name = data.get("name")
    user_id = data.get("user_id")
    result = current_app.closets_manager.create_closet(name, user_id)
    return result

@closets_blueprint.route("/", methods=["DELETE"])
def delete_closet():
    data = request.json
    name = data.get("name")
    user_id = data.get("user_id")
    result = current_app.closets_manager.delete_closet(name, user_id)
    return result

@closets_blueprint.route("/<user_id>", methods=["GET"])
def get_closets_by_user(user_id):
    closets = current_app.closets_manager.get_closets_by_user(user_id)
    return json.dumps(closets, cls=MongoJSONEncoder)

@closets_blueprint.route("/items", methods=["GET"])
def get_items_by_closet():
    user_id = request.args.get("user_id")
    closet = request.args.get("closet")
    items = current_app.closets_manager.get_items_by_closet(user_id, closet)
    return json.dumps(items, cls=MongoJSONEncoder)

@closets_blueprint.route("/<product_id>", methods=["POST"])
def edit_closet_memberships(product_id):
    data = request.json
    closets = data.get("closets")
    user_id = data.get("user_id")
    result = current_app.closets_manager.edit_closet_memberships(closets, user_id, product_id)
    return result