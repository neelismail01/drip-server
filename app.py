from flask import Flask, jsonify, request
from flask_cors import CORS
from helpers.email_scraping_service import get_items
from pymongo import MongoClient
import json
from bson.json_util import dumps, loads

app = Flask(__name__)
cors = CORS(app)

client = MongoClient("mongodb+srv://nikhil_ismail:homKuf-typtim-4sicqo@cluster0.ml9ppgs.mongodb.net/?retryWrites=true&w=majority")
db = client["drip"]

@app.route('/signup', methods=["POST"])
def signup():
    users_collection = db['users']
    data = request.json
    email = data.get('email')
    name = data.get('name')

    # check if user already exists
    existing_user = users_collection.find_one({'email': email})
    if existing_user:
        return 'User already exists', 401

    # insert user into users collection
    user = {
        'email': email,
        'name': name
    }
    users_collection.insert_one(user)

    return 'User signed up', 201

@app.route('/login', methods=["POST"])
def login():
    users_collection = db['users']
    data = request.json
    email = data.get('email')

    # check if user already exists
    existing_user = users_collection.find_one({'email': email})
    if existing_user:
        return 'User logged in', 201

    # User does not exist, return an error message
    return 'Login error - no account associated with this email', 401

@app.route('/items', methods=["GET", "POST", "DELETE"])
def items():
    collection = db['items']
    if request.method == "GET":
        email = request.args.get('email')
        query = {"users": email}
        items = list(collection.find(query))
        json_items = dumps(items)
        return json_items, 201
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
                existing_item_names = [existing_item['item_name'] for existing_item in existing_brand['items']]
                if item['item_name'] not in existing_item_names:
                    # If the item is not already in the brand's item list, add it and increment the purchase count
                    brands_collection.update_one({'_id': existing_brand['_id']}, {'$inc': {'purchasedCount': 1},'$push': {'items': item}})
                else:
                    # If the item is already in the brand's item list, just increment the purchase count
                    brands_collection.update_one({'_id': existing_brand['_id']}, {'$inc': {'purchasedCount': 1}})
            else:
                brand = {'brand_name': item['brand'], 'purchasedCount': 1, 'items': [item]}
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
    collection = db['brands']
    brand = collection.find_one({'brand_name': brand_name})
    if brand:
        items = brand.get('items', [])
        json_items = dumps(items)
        return json_items, 200
    else:
        return "Brand not found", 404

if __name__ == '__main__':
    app.run()