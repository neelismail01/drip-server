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
        return json_items
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
        return "Successfully added items to database", 201
    elif request.method == "DELETE":
        result = collection.delete_many({})
        return f"Deleted {result.deleted_count} documents."

if __name__ == '__main__':
    app.run()