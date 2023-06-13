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

@app.route('/login', methods=["POST"])
def login():
    collection = db['users']
    data = request.json
    email = data.get('email')
    name = data.get('name')

    existing_user = collection.find_one({'email': email})
    if existing_user:
        return 'User already exists in the collection'

    user = {
        'email': email,
        'name': name
    }
    collection.insert_one(user)
    return 'Data received and saved to users collection'

@app.route('/items', methods=["GET", "POST", "DELETE"])
def items():
    collection = db['items']
    if request.method == "GET":
        items = list(collection.find())
        json_items = dumps(items)
        return json_items
    elif request.method == "POST":
        # Get the data from email scraper
        data = get_items()
        result = collection.insert_many(data)
        return "Success", 201
    elif request.method == "DELETE":
        result = collection.delete_many({})
        return f"Deleted {result.deleted_count} documents."

if __name__ == '__main__':
    app.run()