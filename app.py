from flask import Flask, jsonify, request
from flask_cors import CORS
from helpers.email_scraping_service import get_items
from pymongo import MongoClient
from bson import ObjectId
from bson.json_util import dumps

app = Flask(__name__)
cors = CORS(app)

client = MongoClient("mongodb+srv://nikhil_ismail:homKuf-typtim-4sicqo@cluster0.ml9ppgs.mongodb.net/?retryWrites=true&w=majority")
db = client["drip"]

@app.route('/signup', methods=["POST"])
def signup():
    users_collection = db['users']
    data = request.json
    email = data.get('email')

    # check if user already exists
    existing_user = users_collection.find_one({'email': email})
    if existing_user:
        return 'User already exists', 401

    # insert user into users collection
    user = {
        'email': email,
        'name': "",
        'username': "",
        'phone_number': "",
        'profile_pic': "",
        'shopping_preference': "",
        'inbox': []
    }
    users_collection.insert_one(user)

    return 'User signed up', 200

@app.route('/login', methods=["POST"])
def login():
    users_collection = db['users']
    data = request.json
    email = data.get('email')

    # check if user already exists
    existing_user = users_collection.find_one({'email': email})
    if existing_user:
        return 'User logged in', 200

    # User does not exist, return an error message
    return 'Login error - no account associated with this email', 404

@app.route('/inbox', methods=["GET", "POST", "DELETE"])
def inbox():
    users_collection = db['users']
    items_collection = db['items']
    brands_collection = db['brands']
    closet_collection = db['closet']

    if request.method == "POST":
        data = request.json
        email = data.get('email')
        user = users_collection.find_one({'email': email})
        user_items = get_items(email)

        for item in user_items:
            # item logic
            existing_item = items_collection.find_one({'item_name': item['item_name']})
            if existing_item:
                if not closet_collection.find_one({'item_id': existing_item['_id'], 'user_id': user['_id']}):
                    if existing_item['_id'] not in user.get('inbox', []):
                        users_collection.update_one(
                            {'_id': user['_id']},
                            {'$push': {'inbox': existing_item['_id']}}
                        )
            else:
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

@app.route('/closet', methods=["GET", "POST", "DELETE"])
def closet():
    users_collection = db['users']
    items_collection = db['items']
    closet_collection = db['closet']

    if request.method == "POST":
        data = request.json
        email = data.get('email')
        items = data.get('items')
        user = users_collection.find_one({'email': email})
        for item in items:
            item_id = ObjectId(item['_id'])
            closet_collection.insert_one({
                'item_id': item_id,
                'user_id': user['_id'],
                'caption': "",
                'images': []
            })
        return "Successfully added items to the database", 200
    elif request.method == "GET":
        email = request.args.get('email')
        user = users_collection.find_one({'email': email})
        user_id = user['_id']
        closet_items = closet_collection.find({'user_id': ObjectId(user_id)})
        item_ids = [item['item_id'] for item in closet_items]
        if (item_ids):
            items = items_collection.find({'_id': {'$in': item_ids}})
            items_list = list(items)
            for item in items_list:
                item['_id'] = str(item['_id'])
            return jsonify(items_list), 200
        else:
            return [], 201

@app.route('/wishlist', methods=["GET", "POST", "DELETE"])
def wishlist():
    users_collection = db['users']
    items_collection = db['items']
    wishlist_collection = db['wishlist']

    if request.method == "POST":
        data = request.json
        email = data.get('email')
        item = data.get('item')
        user = users_collection.find_one({'email': email})
        item_id = ObjectId(item['_id'])
        if not wishlist_collection.find_one({'user_id': user['_id'], 'item_id': item_id}):
            wishlist_collection.insert_one({
                'item_id': item_id,
                'user_id': user['_id'],
            })
            return "Successfully added item to the wishlist", 200
        else:
            return "Item is already in the wishlist", 400
    elif request.method == "GET":
        email = request.args.get('email')
        user = users_collection.find_one({'email': email})
        user_id = user['_id']
        wishlist_items = wishlist_collection.find({'user_id': ObjectId(user_id)})
        item_ids = [item['item_id'] for item in wishlist_items]
        if (item_ids):
            items = items_collection.find({'_id': {'$in': item_ids}})
            items_list = list(items)
            for item in items_list:
                item['_id'] = str(item['_id'])
            return jsonify(items_list), 200
        else:
            return [], 201
    elif request.method == "DELETE":
        data = request.json
        email = data.get('email')
        item = data.get('item')
        item_id = ObjectId(item['_id'])
        user = users_collection.find_one({'email': email})
        user_id = user['_id']
        wishlist_collection.delete_one({'user_id': user_id, 'item_id': item_id})
        return "Successfully deleted item from wish list", 200

@app.route('/liked_items', methods=["GET", "POST", "DELETE"])
def liked_items():
    users_collection = db['users']
    items_collection = db['items']
    liked_items_collection = db['liked_items']

    if request.method == "POST":
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
    elif request.method == "GET":
        email = request.args.get('email')
        user = users_collection.find_one({'email': email})
        user_id = user['_id']
        liked_items = liked_items_collection.find({'user_id': ObjectId(user_id)})
        item_ids = [item['item_id'] for item in liked_items]
        if (item_ids):
            items = items_collection.find({'_id': {'$in': item_ids}})
            items_list = list(items)
            for item in items_list:
                item['_id'] = str(item['_id'])
            return jsonify(items_list), 200
        else:
            return [], 201
    elif request.method == "DELETE":
        data = request.json
        email = data.get('email')
        item = data.get('item')
        item_id = ObjectId(item['_id'])
        user = users_collection.find_one({'email': email})
        user_id = user['_id']
        liked_items_collection.delete_one({'user_id': user_id, 'item_id': item_id})
        return "Successfully deleted item from liked items", 200

@app.route('/items', methods=["GET", "POST", "DELETE"])
def items():
    collection = db['items']
    if request.method == "GET":
        all_items = list(collection.find())
        for item in all_items:
            item['_id'] = str(item['_id'])
        return jsonify(all_items), 200
    elif request.method == "POST":
        data = request.json
        email = data.get('email')
        # insert items into items collection
        user_items = get_items(email)
        for item in user_items:
            # if item is already in collection, just append user to users array for that item
            existing_item = collection.find_one({'item_name': item['item_name']})
            if existing_item:
                collection.update_one({'_id': existing_item['_id']}, {'$addToSet': {'users': email}})
            else:
                item['users'] = [email]
                collection.insert_one(item)

            brands_collection = db['brands']
            existing_brand = brands_collection.find_one({'brand_name': item['brand']})
            if existing_brand:
                brands_collection.update_one({'_id': existing_brand['_id']}, {'$inc': {'purchasedCount': 1}})
            else:
                brand = {'brand_name': item['brand'], 'purchasedCount': 1}
                brands_collection.insert_one(brand)
        return "Successfully added items to the database", 201
    elif request.method == "DELETE":
        result = collection.delete_many({})
        return f"Deleted {result.deleted_count} documents."

@app.route('/brands', methods=["GET"])
def brands():
    collection = db['brands']
    if request.method == "GET":
        brands = list(collection.find().sort('purchaseCount', -1))
        json_brands = dumps(brands)
        return json_brands, 201

@app.route('/items/<brand_name>', methods=["GET"])
def brand_items(brand_name):
    brands_collection = db['brands']
    items_collection = db['items']
    brand = brands_collection.find_one({'brand_name': brand_name})
    if brand:
        items = items_collection.find({"brand": brand_name})
        json_items = dumps(items)
        return json_items, 200
    else:
        return "Brand not found", 404

if __name__ == '__main__':
    app.run()