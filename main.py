from flask import (
    Flask,
    jsonify,
    request,
)
from flask_session import Session
from flask_cors import CORS
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
app.register_blueprint(items_blueprint, url_prefix="/items")
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