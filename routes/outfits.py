from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)

from bson import ObjectId

outfits_blueprint = Blueprint('outfits', __name__)

@outfits_blueprint.route('/outfits', methods=["GET", "POST", "DELETE"])
def outfits():
    db = current_app.mongo.drip
    users_collection = db['users']
    outfits_collection = db['outfits']

    if request.method == "POST":
        data = request.json
        email = data.get('email')
        items = data.get('items')
        vibe = data.get('vibe')
        caption = data.get('caption')
        pictures = data.get('pictures')

        user = users_collection.find_one({'email': email})
        item_ids = [ObjectId(item["_id"]) for item in items]

        existing_outfit = outfits_collection.find_one({'items': item_ids})
        if existing_outfit:
            return "Outfit already exist in the database", 400

        outfits_collection.insert_one({
            'user_id': user['_id'],
            'items': item_ids,
            'caption': caption,
            'vibe': vibe,
            'images': pictures
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