import json
from flask import (
    Blueprint,
    current_app,
    request
)
from app.utils.MongoJsonEncoder import MongoJSONEncoder

feed_blueprint = Blueprint("feed", __name__)

@feed_blueprint.route("/products", methods=["GET"])
def get_all_products():
    user_id = request.args.get("user_id", "")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 5))
    all_products = current_app.feed_manager.get_all_products(user_id, page, page_size)
    return json.dumps(all_products, cls=MongoJSONEncoder)