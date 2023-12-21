from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)
from helpers.email_scraping_service import get_items

items_blueprint = Blueprint('items', __name__)

@items_blueprint.route('/', methods=["GET", "POST", "DELETE"])
def items():
    db = current_app.mongo.drip
    collection = db['items']
    if request.method == "GET":
        all_items = list(collection.find())
        for item in all_items:
            item['_id'] = str(item['_id'])
        return jsonify(all_items), 200
    elif request.method == "DELETE":
        result = collection.delete_many({})
        return f"Deleted {result.deleted_count} documents."

@items_blueprint.route('/<brand_name>', methods=["GET"])
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

"""
@items_blueprint.route('/inbox', methods=["GET", "POST", "DELETE"])
def inbox():
    db = current_app.mongo.drip
    users_collection = db['users']
    items_collection = db['items']
    brands_collection = db['brands']
    closet_collection = db['closet']

    if request.method == "POST":
        data = request.json
        email = data.get('email')
        user = users_collection.find_one({'email': email})
        gender = user['shopping_preference']
        user_items = get_items(email)

        for item in user_items:
            # item logic
            existing_item = items_collection.find_one({'item_name': item['item_name']})
            if existing_item:
                if not closet_collection.find_one({
                    'item_id': existing_item['_id'],
                    'user_id': user['_id']
                }):
                    if existing_item['_id'] not in user.get('inbox', []):
                        users_collection.update_one(
                            {'_id': user['_id']},
                            {'$push': {'inbox': existing_item['_id']}}
                        )
            else:
                item['gender'] = gender
                new_item = items_collection.insert_one(item)
                item_id = new_item.inserted_id
                users_collection.update_one(
                    {'_id': user['_id']},
                    {'$push': {'inbox': item_id}}
                )
            # brand logic
            existing_brand = brands_collection.find_one({'brand_name': item['brand']})
            if existing_brand:
                brands_collection.update_one({'_id': existing_brand['_id']}, {'$inc': {'purchasedCount': 1}})
            else:
                brand = {'brand_name': item['brand'], 'purchasedCount': 1}
                brands_collection.insert_one(brand)
        return "Successfully added items to the database", 200
    elif request.method == "GET":
        email = request.args.get('email')
        user = users_collection.find_one({'email': email})
        inbox = user.get('inbox', [])
        items = items_collection.find({'_id': {'$in': inbox}})
        items_list = list(items)
        for item in items_list:
                item['_id'] = str(item['_id'])
        return jsonify(items_list), 200
    elif request.method == "DELETE":
        email = request.args.get('email')
        users_collection.update_one(
            {'email': email},
            {'$set': {'inbox': []}}
        )
        return "Successfully deleted items from inbox", 200
"""
