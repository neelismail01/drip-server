from flask import (
    current_app,
    Blueprint,
    jsonify,
    request
)
from bson import ObjectId
user_blueprint = Blueprint('user', __name__)

@user_blueprint.route('/signin', methods=["POST"])
def signin():
    db = current_app.mongo.drip

    data = request.json
    email = data.get("email")
    name = data.get("name")

    # check if user already exists
    existing_user = db.users.find_one({'email': email})
    if existing_user:
        return 'User already exists', 200

    # insert user into users collection
    db.users.insert_one({
        'email': email,
        'name': name,
        'username': None,
        'phone_number': None,
        'profile_pic': None,
        'shopping_preference': None,
        'inbox': []
    })

    return 'User created.', 200

@user_blueprint.route('/signup', methods=["POST"])
def signup():
    db = current_app.mongo.drip
    users_collection = db['users']
    data = request.json
    email = data.get('email')
    name = data.get('name')
    username = data.get('username')
    phone_number = data.get('phone_number')
    profile_pic = data.get('profile_pic')
    shopping_preference = data.get('shopping_preference')

    # check if user already exists
    existing_user = users_collection.find_one({'email': email})
    if existing_user:
        return 'User already exists', 401

    # insert user into users collection
    users_collection.insert_one({
        'email': email,
        'name': name,
        'username': username,
        'phone_number': phone_number,
        'profile_pic': profile_pic,
        'shopping_preference': shopping_preference,
        'inbox': []
    })

    return 'User signed up', 200

@user_blueprint.route('/profile', methods=["PUT"])
def profile():
    db = current_app.mongo.drip
    if request.method == "PUT":
        users_collection = db['users']
        data = request.json
        email = data.get('email')
        profile_picture = data.get('profile_picture')
        
        # check if user already exists
        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            users_collection.update_one(
                {'email': email},
                {'$set': {'profile_picture': profile_picture}}
            )
            return 'User profile updated', 200
        else:
            return 'User not found', 404

@user_blueprint.route('/closet', methods=["GET", "POST", "DELETE"])
def closet():
    db = current_app.mongo.drip
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
        email = request.args.get('email')
        user = users_collection.find_one({'email': email})
        user_id = user['_id']
        
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

@user_blueprint.route('/wishlist', methods=["GET", "POST", "DELETE"])
def wishlist():
    db = current_app.mongo.drip
    users_collection = db['users']
    items_collection = db['items']
    wishlist_collection = db['wishlist']

    if request.method == "POST":
        data = request.json
        email = data.get('email')
        item = data.get('item')
        user = users_collection.find_one({'email': email})
        item_id = ObjectId(item['_id'])
        if not wishlist_collection.find_one({'user_id': user['_id'], 'item_id': item_id}):
            wishlist_collection.insert_one({
                'item_id': item_id,
                'user_id': user['_id'],
            })
            return "Successfully added item to the wishlist", 200
        else:
            return "Item is already in the wishlist", 400
    elif request.method == "GET":
        email = request.args.get('email')
        user = users_collection.find_one({'email': email})
        user_id = user['_id']
        wishlist_items = wishlist_collection.find({'user_id': ObjectId(user_id)})
        item_ids = [item['item_id'] for item in wishlist_items]
        if (item_ids):
            items = items_collection.find({'_id': {'$in': item_ids}})
            items_list = list(items)
            for item in items_list:
                item['_id'] = str(item['_id'])
            return jsonify(items_list), 200
        else:
            return [], 201
    elif request.method == "DELETE":
        data = request.json
        email = data.get('email')
        item = data.get('item')
        item_id = ObjectId(item['_id'])
        user = users_collection.find_one({'email': email})
        user_id = user['_id']
        wishlist_collection.delete_one({'user_id': user_id, 'item_id': item_id})
        return "Successfully deleted item from wish list", 200

@user_blueprint.route('/outfit_wishlist', methods=["GET", "POST", "DELETE"])
def outfit_wishlist():
    db = current_app.mongo.drip
    users_collection = db['users']
    outfits_collection = db['outfits']
    outfit_wishlist_collection = db['outfit_wishlist']

    if request.method == "POST":
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
    elif request.method == "GET":
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
    elif request.method == "DELETE":
        data = request.json
        email = data.get('email')
        outfit = data.get('outfit')
        outfit_id = ObjectId(outfit['_id'])
        user = users_collection.find_one({'email': email})
        user_id = user['_id']
        outfit_wishlist_collection.delete_one({'user_id': user_id, 'outfit_id': outfit_id})
        return "Successfully deleted item from wish list", 200


@user_blueprint.route('/liked_items', methods=["GET", "POST", "DELETE"])
def liked_items():
    db = current_app.mongo.drip
    users_collection = db['users']
    items_collection = db['items']
    liked_items_collection = db['liked_items']

    if request.method == "POST":
        data = request.json
        email = data.get('email')
        item = data.get('item')
        user = users_collection.find_one({'email': email})
        item_id = ObjectId(item['_id'])
        if not liked_items_collection.find_one({'user_id': user['_id'], 'item_id': item_id}):
            liked_items_collection.insert_one({
                'item_id': item_id,
                'user_id': user['_id'],
            })
            return "Successfully added item to liked items", 200
        else:
            return "Item is already in liked items", 400
    elif request.method == "GET":
        email = request.args.get('email')
        user = users_collection.find_one({'email': email})
        user_id = user['_id']
        liked_items = liked_items_collection.find({'user_id': ObjectId(user_id)})
        item_ids = [item['item_id'] for item in liked_items]
        if (item_ids):
            items = items_collection.find({'_id': {'$in': item_ids}})
            items_list = list(items)
            for item in items_list:
                item['_id'] = str(item['_id'])
            return jsonify(items_list), 200
        else:
            return [], 201
    elif request.method == "DELETE":
        data = request.json
        email = data.get('email')
        item = data.get('item')
        item_id = ObjectId(item['_id'])
        user = users_collection.find_one({'email': email})
        user_id = user['_id']
        liked_items_collection.delete_one({'user_id': user_id, 'item_id': item_id})
        return "Successfully deleted item from liked items", 200

@user_blueprint.route('/liked_outfits', methods=["GET", "POST", "DELETE"])
def liked_outfits():
    db = current_app.mongo.drip
    users_collection = db['users']
    outfits_collection = db['outfits']
    liked_outfits_collection = db['liked_outfits']

    if request.method == "POST":
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
    elif request.method == "GET":
        email = request.args.get('email')
        user = users_collection.find_one({'email': email})
        user_id = user['_id']
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
    elif request.method == "DELETE":
        data = request.json
        email = data.get('email')
        outfit = data.get('outfit')
        outfit_id = ObjectId(outfit['_id'])
        user = users_collection.find_one({'email': email})
        user_id = user['_id']
        liked_outfits_collection.delete_one({'user_id': user_id, 'outfit_id': outfit_id})
        return "Successfully deleted item from liked outfits", 200