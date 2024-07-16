import json
from flask import (
    Blueprint,
    current_app,
    request
)
from app.utils.MongoJsonEncoder import MongoJSONEncoder

search_blueprint = Blueprint('search', __name__)

@search_blueprint.route("/", methods=["GET"])
def get_search_results():
    query = request.args.get("query")
    users = current_app.search_manager.search_users(query)
    brands = current_app.search_manager.search_brands(query)
    query_embedding = current_app.text_embeddings_manager.get_openai_text_embedding(query)

@search_blueprint.route("/", methods=["POST"])
def add_search():
    data = request.json
    user_id, profile_id, query, query_type, autocomplete = (
        data.get("user_id"), 
        data.get("profile_id"),
        data.get("query"), 
        data.get("type"),
        data.get("autocomplete")
    )
    current_app.search_manager.add_search(user_id, profile_id, query, query_type, autocomplete)
    return json.dumps("Successfully added search.", cls=MongoJSONEncoder)

@search_blueprint.route("/autocomplete", methods=["GET"])
def get_autocomplete_results():
    query = request.args.get("query")
    users = current_app.search_manager.search_users(query)
    brands = current_app.search_manager.search_brands(query)
    results = users + brands
    sorted_results = list(sorted(results, key=lambda item: item["score"], reverse=True))
    return json.dumps(sorted_results, cls=MongoJSONEncoder)

@search_blueprint.route("/brands", methods=["GET"])
def get_brand_results():
    query = request.args.get("query")
    brands = current_app.search_manager.search_brands(query)
    return json.dumps(brands, cls=MongoJSONEncoder)

@search_blueprint.route("/users", methods=["GET"])
def get_user_results():
    query = request.args.get("query")
    users = current_app.search_manager.search_users(query)
    print(users, query)
    return json.dumps(users, cls=MongoJSONEncoder)
