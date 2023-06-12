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

@app.route('/items', methods=["GET"])
def get_data():

    collection = db['items']
    items = list(collection.find())
    json_items = dumps(items)

    return json_items

@app.route("/items", methods=["POST"])
def insert_data():
    # Get the data from email scraper
    data = get_items()
    collection = db["items"]
    result = collection.insert_many(data)

    return "Success", 201

if __name__ == '__main__':
    app.run()