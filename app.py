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
    items_collection = db['items']
    brands_collection = db['brands']
    data = request.json
    email = data.get('email')
    name = data.get('name')

    # check if user already exists
    existing_user = users_collection.find_one({'email': email})
    if existing_user:
        return 'User already exists', 201

    # insert user into users collection
    user = {
        'email': email,
        'name': name
    }
    users_collection.insert_one(user)

    # insert items into items collection
    user_items = get_items(user["email"])
    for item in user_items:
        # if item is already in collection, just append user to users array for that item
        existing_item = items_collection.find_one({'item_name': item['item_name']})
        if existing_item:
            items_collection.update_one({'_id': existing_item['_id']}, {'$addToSet': {'users': user["email"]}})
        else:
            item['users'] = [user["email"]]
            items_collection.insert_one(item)

        existing_brand = brands_collection.find_one({'brand_name': item['brand']})
        if existing_brand:
            brands_collection.update_one({'_id': existing_brand['_id']}, {'$inc': {'purchasedCount': 1}})
        else:
            brand = {'brand_name': item['brand'], 'purchasedCount': 1}
            brands_collection.insert_one(brand)

    return 'User signed up - data received and saved to items collection', 201

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
        print(items)
        json_items = dumps(items)
        return json_items
    # change to update vs insert
    elif request.method == "POST":
        # Get the data from email scraper
        data = get_items("")
        result = collection.insert_many(data)
        return "Success", 201
    elif request.method == "DELETE":
        result = collection.delete_many({})
        return f"Deleted {result.deleted_count} documents."

if __name__ == '__main__':
    app.run()