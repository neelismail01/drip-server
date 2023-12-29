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

outfits_blueprint = Blueprint('outfits', __name__)

# Set the path to your service account key JSON file
#service_account_key_path = '../service_account_key.json'
# Set the environment variable
#os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_key_path

# Initialize GCS client
def get_storage_client():
    return storage.Client(project="drip-382808")

def upload_image_to_gcs(image_data, bucket_name, destination_blob_name):
    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    # Upload the image data to GCS
    blob.upload_from_string(image_data, content_type='image/jpeg')
    # Get the URL of the uploaded image
    return blob.public_url

@outfits_blueprint.route('/outfits', methods=["GET", "POST", "DELETE"])
def outfits():
    db = current_app.mongo.drip
    users_collection = db['users']
    outfits_collection = db['outfits']

    if request.method == "POST":
        data = request.json
        email = data.get('email')
        items = data.get('items')
        tags = data.get('tags')
        caption = data.get('caption')
        pictures = data.get('pictures')

        image_bytes = base64.b64decode(pictures)
        gcs_picture_url = upload_image_to_gcs(image_bytes, 'drip-bucket-1', 'image1.jpg')

        user = users_collection.find_one({'email': email})
        item_ids = [ObjectId(item["_id"]) for item in items]

        existing_outfit = outfits_collection.find_one({'items': item_ids})
        if existing_outfit:
            return "Outfit already exist in the database", 400

        outfits_collection.insert_one({
            'user_id': user['_id'],
            'items': item_ids,
            'caption': caption,
            'tags': tags,
            'images': [gcs_picture_url]
        })
        return "Successfully added items to the database", 200
    elif request.method == "GET":
        email = request.args.get('email')
        user = users_collection.find_one({'email': email})
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