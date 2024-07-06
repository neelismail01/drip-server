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
        return json.dumps(brands, cls=MongoJSONEncoder), 200
    
@brands_blueprint.route('/<brand_name>', methods=["GET"])
def brand(brand_name):
    db = current_app.mongo.drip
    brands_collection = db['brands']
    users_collection = db['users']
    social_graph_collection = db['social_graph']

    if request.method == "GET":
        brand = brands_collection.find_one({'name': brand_name})
        if not brand:
            return {}, 200
        return json.dumps(brand, cls=MongoJSONEncoder), 200
    
@brands_blueprint.route('/outfit_brands/<user_id>', methods=["GET"])
def outfit_brands(user_id):
    db = current_app.mongo.drip
    collection = db['brands']
    social_collection = db['social_graph']
    if request.method == "GET":
        brand_names_param = request.args.get("brand_names", "")
        decoded_brand_names = [unquote(name) for name in brand_names_param.split(",")]
        query = {"name": {"$in": decoded_brand_names}}
        brands = list(collection.find(query))
        user_object_id = ObjectId(user_id)
        mutuals_set = set()
        follower_count = 0
        for brand in brands:
            count = social_collection.count_documents({ "followee_id": brand['_id'], "status": "SUCCESSFUL" })
            brand['followerCount'] = count
            follower_count = follower_count + count
            mutual_followers = list(social_collection.aggregate([
                # Match documents where the followee is either user1 or user2
                {'$match': {
                    'followee_id': {'$in': [user_object_id, brand['_id']]}
                }},
                # Group by follower_id and count the number of documents
                {'$group': {
                    '_id': '$follower_id',
                    'count': {'$sum': 1}
                }},
                # Filter to keep only followers who follow both users
                {'$match': {
                    'count': 2
                }},
                # Look up the user details from the users collection
                {'$lookup': {
                    'from': 'users',
                    'localField': '_id',
                    'foreignField': '_id',
                    'as': 'user_details'
                }},
                # Unwind the user_details array
                {'$unwind': '$user_details'},
                # Project only the fields we want
                {'$project': {
                    '_id': 1,
                    'username': '$user_details.username',
                    'name': '$user_details.name',
                    'profile_picture': '$user_details.profile_picture'
                }}
            ]))
            for follower in mutual_followers:
                follower['_id'] = str(follower['_id'])
                mutuals_set.add(frozenset(follower.items()))
            brand['mutualFollowers'] = mutual_followers

        mutuals_list = [dict(follower) for follower in mutuals_set]

        return json.dumps({'brands': brands, 'mutual_followers': mutuals_list, 'follower_count': follower_count}, cls=MongoJSONEncoder), 200

@brands_blueprint.route('/closet/<brand_name>', methods=["GET"])
def brand_closet(brand_name):
    db = current_app.mongo.drip
    brands_collection = db['brands']
    items_collection = db['items']

    brand = brands_collection.find_one({'name': brand_name})
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

    brand = brands_collection.find_one({'name': brand_name})
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

    brand = brands_collection.find_one({'name': brand_name})
    if not brand:
        return "Brand not found", 404

    items = list(items_collection.find({"brand": brand_name}))
    item_ids = [item['_id'] for item in items]
    liked_count = liked_items_collection.count_documents({'post_id': {'$in': item_ids}})
    
    return jsonify({'liked_count': liked_count}), 200

@brands_blueprint.route('/liked_items/<brand_name>', methods=["GET"])
def liked_items(brand_name):
    db = current_app.mongo.drip
    brands_collection = db['brands']
    items_collection = db['items']
    liked_items_collection = db['liked_items']

    brand = brands_collection.find_one({'name': brand_name})
    if not brand:
        return "Brand not found", 404

    items = list(items_collection.find({"brand": brand_name}))
    item_ids = [item['_id'] for item in items]

    # Count likes for each item
    liked_items_cursor = liked_items_collection.aggregate([
        {'$match': {'post_id': {'$in': item_ids}}},
        {'$group': {'_id': '$post_id', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ])

    sorted_liked_items = []
    for doc in liked_items_cursor:
        item = items_collection.find_one({'_id': doc['_id']})
        if item:
            item['_id'] = str(item['_id'])
            sorted_liked_items.append(item)

    return json.dumps(sorted_liked_items, cls=MongoJSONEncoder), 200

@brands_blueprint.route('/top_shoppers/<brand_name>', methods=["GET"])
def get_top_shoppers(brand_name):
    db = current_app.mongo.drip
    brands_collection = db['brands']
    items_collection = db['items']
    users_collection = db['users']

    # Find the brand document
    brand = brands_collection.find_one({'name': brand_name})
    if not brand:
        return "Brand not found", 404

    # Find items belonging to the brand
    items = list(items_collection.find({"brand": brand_name}))

    # Count item ownership per user
    user_items_count = {}
    for item in items:
        user_id = item['user_id']
        if user_id in user_items_count:
            user_items_count[user_id] += 1
        else:
            user_items_count[user_id] = 1

    # Sort users by the number of items owned from this brand (descending)
    sorted_users = sorted(user_items_count.items(), key=lambda x: x[1], reverse=True)

    # Fetch user details for the top 5 users (or less if fewer users own the brand)
    top_shoppers = []
    for user_id, item_count in sorted_users[:5]:
        user = users_collection.find_one({'_id': user_id})
        if user:
            user['_id'] = str(user['_id'])  # Convert ObjectId to string for JSON serialization
            user['item_count'] = item_count
            top_shoppers.append(user)

    return json.dumps(top_shoppers, cls=MongoJSONEncoder), 200
