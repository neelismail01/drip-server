from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)
from bson import ObjectId

items_blueprint = Blueprint('items', __name__)

@items_blueprint.route('/', methods=["GET", "POST", "DELETE"])
def items():
    db = current_app.mongo.drip
    items_collection = db['items']
    if request.method == "GET":
        all_items = list(items_collection.find())
        for item in all_items:
            item['_id'] = str(item['_id'])
        return jsonify(all_items), 200
    elif request.method == "DELETE":
        result = items_collection.delete_many({})
        return f"Deleted {result.deleted_count} documents."

@items_blueprint.route('/liked', methods=["GET"])
def get_liked_items():
    db = current_app.mongo.drip
    closet_collection = db['collection']
    items_collection = db['items']
    liked_items_collection = db['liked_items']

    user_id = request.args.get('user_id')
    liked_items = liked_items_collection.find({'user_id': ObjectId(user_id)})
    item_ids = [item['item_id'] for item in liked_items]

    if item_ids:
        closet_list = []
        closet_items = []
        for item_id in item_ids:
            closet_doc = closet_collection.find({'item_id': item_id})
            closet_items.append(closet_doc)

        for closet_item in closet_items:
            item_doc = items_collection.find_one({'_id': closet_item['item_id']})
            if item_doc:
                item_doc['_id'] = str(item_doc['_id'])
                closet_item['_id'] = str(closet_item['_id'])
                closet_item['item'] = item_doc
                closet_item['user_id'] = str(closet_item['user_id'])
                del closet_item['item_id']
                closet_list.append(closet_item)

        return jsonify(closet_list), 200
    else:
        return jsonify([]), 201

@items_blueprint.route('/liked', methods=["POST"])
def create_liked_items():
    db = current_app.mongo.drip
    users_collection = db['users']
    liked_items_collection = db['liked_items']

    data = request.json
    email = data.get('email')
    item = data.get('item')
    user = users_collection.find_one({'email': email})
    item_id = ObjectId(item['_id'])
    if not liked_items_collection.find_one({'user_id': user['_id'], 'item_id': item_id}):
        liked_items_collection.insert_one({
            'item_id': item_id,
            'user_id': user['_id'],
        })
        return "Successfully added item to liked items", 200
    else:
        return "Item is already in liked items", 400

@items_blueprint.route('/liked', methods=["DELETE"])
def delete_liked_items():
    db = current_app.mongo.drip
    users_collection = db['users']
    liked_items_collection = db['liked_items']

    data = request.json
    email = data.get('email')
    item = data.get('item')
    item_id = ObjectId(item['_id'])
    user = users_collection.find_one({'email': email})
    user_id = user['_id']
    liked_items_collection.delete_one({'user_id': user_id, 'item_id': item_id})
    return "Successfully deleted item from liked items", 200