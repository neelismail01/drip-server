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

@outfits_blueprint.route('/', methods=["GET", "POST", "DELETE"])
def outfits():
    db = current_app.mongo.drip
    users_collection = db['users']
    outfits_collection = db['outfits']

    if request.method == "POST":
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
    elif request.method == "GET":
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