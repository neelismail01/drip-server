from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)

from bson.json_util import dumps

brands_blueprint = Blueprint('brands', __name__)

@brands_blueprint.route('/', methods=["GET"])
def all_brands():
    db = current_app.mongo.drip
    collection = db['brands']
    if request.method == "GET":
        brands = list(collection.find().sort('purchaseCount', -1))
        json_brands = dumps(brands)
        return json_brands, 201
    
@brands_blueprint.route('/<brand_name>', methods=["GET"])
def brand(brand_name):
    db = current_app.mongo.drip
    collection = db['brands']
    if request.method == "GET":
        brand = collection.find_one({'brand_name': brand_name})
        if not brand:
            return {}, 200
        brand['_id'] = str(brand['_id'])
        return jsonify(brand), 200
    
@brands_blueprint.route('/outfit_brands', methods=["GET"])
def outfit_brands():
    db = current_app.mongo.drip
    collection = db['brands']
    if request.method == "GET":
        brand_names = request.args.getlist("brand_names[]")
        query = {"brand_name": {"$in": brand_names}}
        brands = list(collection.find(query))
        for brand in brands:
            brand['_id'] = str(brand['_id'])
        return jsonify(brands), 200

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
    closet_collection = db['closet']

    # Find the brand
    brand = brands_collection.find_one({'brand_name': brand_name})
    if not brand:
        return "Brand not found", 404
    
    # Find items for the brand
    items = list(items_collection.find({"brand": brand_name}))
    item_ids = [item['_id'] for item in items]
    
    # Find closet documents with the found item IDs
    closet_items = list(closet_collection.find({'item_id': {'$in': item_ids}}))
    
    # Create a dictionary for items with item_id as the key
    items_dict = {item['_id']: item for item in items}
    
    # Replace item_id with the complete item document in closet documents
    for closet_item in closet_items:
        item_id = closet_item['item_id']
        item = items_dict.get(item_id)
        
        # Ensure the item_id is converted to a string
        if item:
            item['_id'] = str(item['_id'])
        
        closet_item['item'] = item
        closet_item.pop('item_id', None)
        closet_item['_id'] = str(closet_item['_id'])
        closet_item['user_id'] = str(closet_item['user_id'])  # Convert user_id to string
    
    return jsonify(closet_items), 200