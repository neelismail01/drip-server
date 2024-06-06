from flask import (
    Flask,
    jsonify,
    request,
)
from flask_session import Session
from flask_cors import CORS
from helpers.email_scraping_service import get_items
from pymongo import MongoClient
from bson import ObjectId
from bson.json_util import dumps
import os
import certifi

from constants import MONGO_URI

from routes.brands import brands_blueprint
from routes.items import items_blueprint
from routes.outfits import outfits_blueprint
from routes.search import search_blueprint
from routes.user import user_blueprint
from routes.social import social_blueprint
from routes.assistant import assistant_blueprint

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['MONGO_URI'] = MONGO_URI

# Initialize the MongoDB client
mongo_client = MongoClient(app.config['MONGO_URI'], tlsCAFile=certifi.where())
app.mongo = mongo_client

Session(app)
cors = CORS(app)

## To be deleted...
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["drip"]

# Register the blueprint with the app
app.register_blueprint(brands_blueprint, url_prefix="/brands")
app.register_blueprint(items_blueprint)
app.register_blueprint(outfits_blueprint, url_prefix="/outfits")
app.register_blueprint(search_blueprint, url_prefix="/search")
app.register_blueprint(social_blueprint, url_prefix='/social')
app.register_blueprint(user_blueprint, url_prefix='/user')
app.register_blueprint(assistant_blueprint, url_prefix="/assistant")

@app.route('/similar_items', methods=['GET'])
def similar_items():
    collection = db["items"]
    tag = request.args.get('tag')
    items = collection.find({"tag": tag})
    items_list = list(items)
    for item in items_list:
            item['_id'] = str(item['_id'])
    return jsonify(items_list), 200

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
        gender = user['shopping_preference']
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
            item_id = ObjectId(item['product']['_id'])
            closet_collection.insert_one({
                'item_id': item_id,
                'user_id': user['_id'],
                'caption': item['caption'],
                'images': item['pictures']
            })
        return "Successfully added items to the database", 200
    elif request.method == "GET":
        user_id = request.args.get('user_id')
        closet_documents = closet_collection.find({'user_id': ObjectId(user_id)})
        closet_items = []

        for closet_doc in closet_documents:
            item_id = closet_doc['item_id']
            item_doc = items_collection.find_one({'_id': item_id})

            if item_doc:
                item_doc['_id'] = str(item_doc['_id'])
                closet_item = {
                    'closet_id': str(closet_doc['_id']),
                    'item': item_doc,
                    'caption': closet_doc['caption'],
                    'images': closet_doc['images']
                }
                closet_items.append(closet_item)

        return jsonify(closet_items), 200

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
    
@app.route('/outfit_wishlist', methods=["GET", "POST", "DELETE"])
def outfit_wishlist():
    users_collection = db['users']
    outfits_collection = db['outfits']
    outfit_wishlist_collection = db['outfit_wishlist']

    if request.method == "POST":
        data = request.json
        email = data.get('email')
        outfit = data.get('outfit')
        user = users_collection.find_one({'email': email})
        outfit_id = ObjectId(outfit['_id'])
        if not outfit_wishlist_collection.find_one({'user_id': user['_id'], 'outfit_id': outfit_id}):
            outfit_wishlist_collection.insert_one({
                'outfit_id': outfit_id,
                'user_id': user['_id'],
            })
            return "Successfully added outfit to the wishlist", 200
        else:
            return "Outfit is already in the wishlist", 400
    elif request.method == "GET":
        email = request.args.get('email')
        user = users_collection.find_one({'email': email})
        user_id = user['_id']
        wishlist_outfits = outfit_wishlist_collection.find({'user_id': ObjectId(user_id)})
        outfit_ids = [outfit['outfit_id'] for outfit in wishlist_outfits]
        if (outfit_ids):
            outfits = list(outfits_collection.find({'_id': {'$in': outfit_ids}}))
            for outfit in outfits:
                outfit['_id'] = str(outfit['_id'])
                outfit['user_id'] = str(outfit['user_id'])
                for i in range(len(outfit['items'])):
                    outfit['items'][i] = str(outfit['items'][i])
            return jsonify(outfits), 200
        else:
            return [], 201
    elif request.method == "DELETE":
        data = request.json
        email = data.get('email')
        outfit = data.get('outfit')
        outfit_id = ObjectId(outfit['_id'])
        user = users_collection.find_one({'email': email})
        user_id = user['_id']
        outfit_wishlist_collection.delete_one({'user_id': user_id, 'outfit_id': outfit_id})
        return "Successfully deleted item from wish list", 200

@app.route('/liked_items', methods=["GET", "POST", "DELETE"])
def liked_items():
    closet_collection = db['collection']
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

            print(closet_list)
            return jsonify(closet_list), 200
        else:
            return jsonify([]), 201
    elif request.method == "DELETE":
        data = request.json
        email = data.get('email')
        item = data.get('item')
        item_id = ObjectId(item['_id'])
        user = users_collection.find_one({'email': email})
        user_id = user['_id']
        liked_items_collection.delete_one({'user_id': user_id, 'item_id': item_id})
        return "Successfully deleted item from liked items", 200
    
@app.route('/liked_outfits', methods=["GET", "POST", "DELETE"])
def liked_outfits():
    users_collection = db['users']
    outfits_collection = db['outfits']
    liked_outfits_collection = db['liked_outfits']

    if request.method == "POST":
        data = request.json
        email = data.get('email')
        outfit = data.get('outfit')
        user = users_collection.find_one({'email': email})
        outfit_id = ObjectId(outfit['_id'])
        if not liked_outfits_collection.find_one({'user_id': user['_id'], 'outfit_id': outfit_id}):
            liked_outfits_collection.insert_one({
                'outfit_id': outfit_id,
                'user_id': user['_id'],
            })
            return "Successfully added item to liked outfits", 200
        else:
            return "Item is already in liked outfits", 400
    elif request.method == "GET":
        user_id = request.args.get('user_id')
        liked_outfits = liked_outfits_collection.find({'user_id': ObjectId(user_id)})
        outfit_ids = [outfit['outfit_id'] for outfit in liked_outfits]
        if (outfit_ids):
            outfits = list(outfits_collection.find({'_id': {'$in': outfit_ids}}))
            for outfit in outfits:
                outfit['_id'] = str(outfit['_id'])
                outfit['user_id'] = str(outfit['user_id'])
                for i in range(len(outfit['items'])):
                    outfit['items'][i] = str(outfit['items'][i])
            return jsonify(outfits), 200
        else:
            return [], 201
    elif request.method == "DELETE":
        data = request.json
        email = data.get('email')
        outfit = data.get('outfit')
        outfit_id = ObjectId(outfit['_id'])
        user = users_collection.find_one({'email': email})
        user_id = user['_id']
        liked_outfits_collection.delete_one({'user_id': user_id, 'outfit_id': outfit_id})
        return "Successfully deleted item from liked outfits", 200

@app.route('/items', methods=["GET", "POST", "DELETE"])
def items():
    collection = db['items']
    if request.method == "GET":
        all_items = list(collection.find())
        for item in all_items:
            item['_id'] = str(item['_id'])
        return jsonify(all_items), 200
    elif request.method == "DELETE":
        result = collection.delete_many({})
        return f"Deleted {result.deleted_count} documents."

@app.route('/all_brands', methods=["GET"])
def all_brands():
    collection = db['brands']
    if request.method == "GET":
        brands = list(collection.find().sort('purchaseCount', -1))
        json_brands = dumps(brands)
        return json_brands, 201
    
@app.route('/brands/<brand_name>', methods=["GET"])
def brand(brand_name):
    collection = db['brands']
    if request.method == "GET":
        brand = collection.find_one({'brand_name': brand_name})
        brand['_id'] = str(brand['_id'])
        return jsonify(brand), 200
    
@app.route('/outfit_brands', methods=["GET"])
def outfit_brands():
    collection = db['brands']
    if request.method == "GET":
        brand_names = request.args.getlist("brand_names[]")
        query = {"brand_name": {"$in": brand_names}}
        brands = list(collection.find(query))
        for brand in brands:
            brand['_id'] = str(brand['_id'])
        return jsonify(brands), 200

@app.route('/items/<brand_name>', methods=["GET"])
def brand_items(brand_name):
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

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(debug=True, port=8080)
    ##get_items("nikhil.ismail20@gmail.com")