import json
from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)
from bson.json_util import dumps
from bson.objectid import ObjectId
from urllib.parse import unquote
from app.utils.MongoJsonEncoder import MongoJSONEncoder

brands_blueprint = Blueprint('brands', __name__)

@brands_blueprint.route('/search', methods=["GET"])
def search_brands():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Search query is required"}), 400
    result, status_code = current_app.brand_search_manager.search_brands(query)
    return json.dumps(result, cls=MongoJSONEncoder), status_code

@brands_blueprint.route('/', methods=["GET"])
def all_brands():
    db = current_app.mongo.drip
    collection = db['brands']
    if request.method == "GET":
        brands = list(collection.find().sort('purchaseCount', -1))
        json_brands = dumps(brands)
        return json_brands, 201
    
@brands_blueprint.route('/<brand_name>/<my_user_id>', methods=["GET"])
def brand(brand_name, my_user_id):
    db = current_app.mongo.drip
    brands_collection = db['brands']
    users_collection = db['users']
    social_graph_collection = db['social_graph']

    if request.method == "GET":
        brand = brands_collection.find_one({'brand_name': brand_name})
        if not brand:
            return {}, 200
            
        brand['_id'] = str(brand['_id'])
        follower_ids = brand['followers']
        follower_object_ids = [ObjectId(follower_id) for follower_id in follower_ids]
        users = []
        for user_id in follower_object_ids:
            user = users_collection.find_one({'_id': user_id})
            if user:
                is_following = social_graph_collection.find_one({
                    "follower_id": my_user_id,
                    "followee_id": str(user_id),
                    "status": "SUCCESSFUL"
                }) is not None

                user_data = {
                    'id': str(user_id),
                    'name': user.get('name', ''),
                    'email': user.get('email', ''),
                    'username': user.get('username', ''),
                    'profile_pic': user.get('profile_picture', ''),
                    "is_following": is_following
                }
                users.append(user_data)
        brand['followers'] = users
        return jsonify(brand), 200
    
@brands_blueprint.route('/outfit_brands', methods=["GET"])
def outfit_brands():
    db = current_app.mongo.drip
    collection = db['brands']
    if request.method == "GET":
        brand_names = request.args.getlist("brand_names[]")
        decoded_brand_names = [unquote(name) for name in brand_names]
        query = {"brand_name": {"$in": decoded_brand_names}}
        brands = list(collection.find(query))
        for brand in brands:
            brand['_id'] = str(brand['_id'])
        return json.dumps(brands, cls=MongoJSONEncoder), 200

@brands_blueprint.route('/items/<brand_name>', methods=["GET"])
def brand_items(brand_name):
    db = current_app.mongo.drip
    brands_collection = db['brands']
    items_collection = db['items']
    brand = brands_collection.find_one({'brand_name': brand_name})
    if brand:
        items = list(items_collection.find({"brand": brand_name}))
        for item in items:
            item['_id'] = str(item['_id'])
        return jsonify(items), 200
    else:
        return "Brand not found", 404

@brands_blueprint.route('/closet/<brand_name>', methods=["GET"])
def brand_closet(brand_name):
    db = current_app.mongo.drip
    brands_collection = db['brands']
    items_collection = db['items']

    brand = brands_collection.find_one({'brand_name': brand_name})
    if not brand:
        return "Brand not found", 404
    
    items = list(items_collection.find({"brand": brand_name}))
    
    return json.dumps(items, cls=MongoJSONEncoder), 200

@brands_blueprint.route('/outfits/<brand_name>', methods=["GET"])
def brand_outfits(brand_name):
    db = current_app.mongo.drip
    brands_collection = db['brands']
    outfits_collection = db['outfits']
    items_collection = db['items']

    brand = brands_collection.find_one({'brand_name': brand_name})
    if not brand:
        return "Brand not found", 404

    items = list(items_collection.find({"brand": brand_name}))
    item_ids = [item['_id'] for item in items]
    
    # Find outfits that contain at least one item from the brand
    outfits = list(outfits_collection.find({'items': {'$in': item_ids}}))
    
    # Fetch all items used in the outfits
    all_item_ids = {item_id for outfit in outfits for item_id in outfit['items']}
    all_items = list(items_collection.find({'_id': {'$in': list(all_item_ids)}}))
    items_dict = {item['_id']: item for item in all_items}
    
    # Replace item_id with the complete item document in outfit documents
    for outfit in outfits:
        outfit['items'] = [items_dict.get(item_id) for item_id in outfit['items'] if items_dict.get(item_id)]
        
        outfit['_id'] = str(outfit['_id'])
        outfit['user_id'] = str(outfit['user_id'])
        for item in outfit['items']:
            item['_id'] = str(item['_id'])

    return json.dumps(outfits, cls=MongoJSONEncoder), 200

@brands_blueprint.route('/liked_count/<brand_name>', methods=["GET"])
def liked_count(brand_name):
    db = current_app.mongo.drip
    brands_collection = db['brands']
    items_collection = db['items']
    liked_items_collection = db['liked_items']

    brand = brands_collection.find_one({'brand_name': brand_name})
    if not brand:
        return "Brand not found", 404

    items = list(items_collection.find({"brand": brand_name}))
    item_ids = [item['_id'] for item in items]
    liked_count = liked_items_collection.count_documents({'item_id': {'$in': item_ids}})
    
    return jsonify({'liked_count': liked_count}), 200

@brands_blueprint.route('/liked_items/<brand_name>', methods=["GET"])
def liked_items(brand_name):
    db = current_app.mongo.drip
    brands_collection = db['brands']
    items_collection = db['items']
    liked_items_collection = db['liked_items']

    brand = brands_collection.find_one({'brand_name': brand_name})
    if not brand:
        return "Brand not found", 404

    items = list(items_collection.find({"brand": brand_name}))
    item_ids = [item['_id'] for item in items]

    # Count likes for each item
    liked_items_cursor = liked_items_collection.aggregate([
        {'$match': {'item_id': {'$in': item_ids}}},
        {'$group': {'_id': '$item_id', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ])

    sorted_liked_items = []
    for doc in liked_items_cursor:
        item = items_collection.find_one({'_id': doc['_id']})
        if item:
            item['_id'] = str(item['_id'])
            sorted_liked_items.append(item)

    return json.dumps(sorted_liked_items, cls=MongoJSONEncoder), 200
