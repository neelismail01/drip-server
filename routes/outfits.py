from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)
import os
import base64
from google.cloud import storage
from bson import ObjectId
from datetime import datetime

outfits_blueprint = Blueprint('outfits', __name__)

# Initialize GCS client
def get_storage_client():
    return storage.Client(project="drip-382808")

def upload_media_to_gcs(image_data, bucket_name, destination_blob_name, content_type):
    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    # Upload the image data to GCS
    blob.upload_from_string(image_data, content_type=content_type)
    # Get the URL of the uploaded image
    return blob.public_url

@outfits_blueprint.route('/', methods=["GET"])
def get_outfits():
    db = current_app.mongo.drip
    users_collection = db['users']
    outfits_collection = db['outfits']

    user_id = request.args.get('user_id')
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    if user is None:
        return jsonify({"error": "User not found"}), 404
    
    pipeline = [
        {
            '$match': {'user_id': user['_id']}
        },
        {
            '$lookup': {
                'from': 'items',
                'localField': 'items',
                'foreignField': '_id',
                'as': 'items'
            }
        }
    ]
    outfits = list(outfits_collection.aggregate(pipeline))
    for outfit in outfits:
        outfit['_id'] = str(outfit['_id'])
        outfit['user_id'] = str(outfit['user_id'])
        for item in outfit['items']:
            item['_id'] = str(item['_id'])

    return jsonify(outfits), 200

@outfits_blueprint.route('/', methods=["POST"])
def create_outfit():
    db = current_app.mongo.drip
    users_collection = db['users']
    outfits_collection = db['outfits']

    data = request.json
    email = data.get('email')
    items = data.get('items')
    tags = data.get('tags')
    name = data.get('name')
    caption = data.get('caption')
    pictures = data.get('pictures')

    user = users_collection.find_one({'email': email})
    item_ids = [ObjectId(item["_id"]) for item in items]

    existing_outfit = outfits_collection.find_one({'items': item_ids})
    if existing_outfit:
        return "Outfit already exist in the database", 400
    
    # upload images to GCS and get public URLs
    media_urls = []
    for media in pictures:
        if media["type"] == "image":
            image_bytes = base64.b64decode(media["data"])
            destination = "outfit_" + str(user['_id']) + "_" + str(datetime.now()) + ".jpg"
            gcs_media_url = upload_media_to_gcs(image_bytes, 'drip-bucket-1', destination, 'image/jpeg')
            media_urls.append(gcs_media_url)
        elif media["type"] == "video":
            video_bytes = base64.b64decode(media["data"])
            destination = "outfit_" + str(user['_id']) + "_" + str(datetime.now()) + ".mp4"
            gcs_media_url = upload_media_to_gcs(video_bytes, 'drip-bucket-1', destination, 'video/mp4')
            media_urls.append(gcs_media_url)
        else:
            print("Unsupported media format")

    outfits_collection.insert_one({
        'user_id': user['_id'],
        'items': item_ids,
        'name': name,
        'caption': caption,
        'tags': tags,
        'images': media_urls
    })
    return "Successfully added items to the database", 200

@outfits_blueprint.route('/liked', methods=["GET"])
def get_liked_outfits():
    db = current_app.mongo.drip
    outfits_collection = db['outfits']
    liked_outfits_collection = db['liked_outfits']

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

@outfits_blueprint.route('/liked', methods=["POST"])
def create_liked_outfit():
    db = current_app.mongo.drip
    users_collection = db['users']
    liked_outfits_collection = db['liked_outfits']

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

@outfits_blueprint.route('/liked', methods=["DELETE"])
def delete_liked_outfit():
    db = current_app.mongo.drip
    users_collection = db['users']
    liked_outfits_collection = db['liked_outfits']

    data = request.json
    email = data.get('email')
    outfit = data.get('outfit')
    outfit_id = ObjectId(outfit['_id'])
    user = users_collection.find_one({'email': email})
    user_id = user['_id']
    liked_outfits_collection.delete_one({'user_id': user_id, 'outfit_id': outfit_id})
    return "Successfully deleted item from liked outfits", 200

@outfits_blueprint.route('/wishlist', methods=["GET"])
def get_wishlist_outfits():
    db = current_app.mongo.drip
    users_collection = db['users']
    outfits_collection = db['outfits']
    outfit_wishlist_collection = db['outfit_wishlist']

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

@outfits_blueprint.route('/wishlist', methods=["POST"])
def create_wishlist_outfit():
    db = current_app.mongo.drip
    users_collection = db['users']
    outfit_wishlist_collection = db['outfit_wishlist']

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

@outfits_blueprint.route('/wishlist', methods=["DELETE"])
def delete_wishlist_outfit():
    db = current_app.mongo.drip
    users_collection = db['users']
    outfit_wishlist_collection = db['outfit_wishlist']

    data = request.json
    email = data.get('email')
    outfit = data.get('outfit')
    outfit_id = ObjectId(outfit['_id'])
    user = users_collection.find_one({'email': email})
    user_id = user['_id']
    outfit_wishlist_collection.delete_one({'user_id': user_id, 'outfit_id': outfit_id})
    return "Successfully deleted item from wish list", 200
