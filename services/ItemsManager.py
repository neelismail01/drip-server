from bson import ObjectId
from datetime import datetime
from services.CloudStorageManager import cloud_storage_manager
from googleapiclient.discovery import build
import re
import base64

class ItemsManager:
    def __init__(self, mongo_client):
        self.db = mongo_client["drip"]
        self.users_collection = self.db["users"]
        self.items_collection = self.db["items"]
        self.liked_items_collection = self.db["liked_items"]
        self.wishlist_items_collection = self.db["wishlist_items"]
        self.brands_collection = self.db['brands']

    def get_brand_website_link(self, brand):
        API_KEY = "AIzaSyDLvRwgY8OXyNb4a7bas4aT-gXQvHkRwTE"
        SEARCH_ENGINE_ID = "d1062150d54a04ec6"

        brand = "".join(brand.split()).lower()
        query = "{} official website".format(brand)
        service = build("customsearch", "v1", developerKey=API_KEY)
        result = service.cse().list(q=query, cx=SEARCH_ENGINE_ID).execute()
        brand_website_link = None
        if "items" in result:
            for item in result['items']:
                link = item['link']
                if re.search("(^https?://(?:www\.)?{}[^/]*\.[a-z]+)".format(re.escape(brand)), link):
                    brand_website_link = link
                    break

        return brand_website_link

    def get_all_items(self):
        items = list(self.items_collection.find({}))
        return items

    def create_item(self, item):
        user_object_id = ObjectId(item['user_id'])
        user = self.users_collection.find_one({'_id': user_object_id})
        
        media_urls = []
        for media in item['images']:
            if media["type"] == "image":
                image_bytes = base64.b64decode(media["data"])
                destination = "item_{}_{}".format(item['user_id'], str(datetime.now()))
                gcs_media_url = cloud_storage_manager.upload_media_to_gcs(image_bytes, destination, 'image/jpeg')
                media_urls.append(gcs_media_url)
            else:
                print("Unsupported media format")
        item['images'] = media_urls
        item['user_id'] = user_object_id
        item['gender'] = user['preference']
        item['product_page_link'] = self.get_brand_website_link(item['brand'])
        item['date_created'] = datetime.utcnow()
        result = self.items_collection.insert_one(item)

        existing_brand = self.brands_collection.find_one({'brand_name': item['brand']})
        if existing_brand:
            if item['user_id'] not in existing_brand['followers']:
                self.brands_collection.update_one(
                    {'_id': existing_brand['_id']},
                    {'$push': {'followers': item['user_id']}}
                )
        else:
            new_brand = {
                'brand_name': item['brand'],
                'username': "",
                'profile_pic': "https://storage.googleapis.com/drip-bucket-1/default_brand_profile_pic.jpg", 
                'followers': [item['user_id']]
            }
            self.brands_collection.insert_one(new_brand)

        return "Item was created" if result else "Error creating item"

    def get_user_items(self, user_id):
        user_object_id = ObjectId(user_id)
        user_items = list(self.items_collection.find({'user_id': user_object_id}))
        return user_items

    def get_liked_items(self, user_id):
        user_object_id = ObjectId(user_id)
        liked_items = list(self.liked_items_collection.aggregate([
            { "$match": { "user_id": user_object_id } },
            {
                "$lookup": {
                    "from": "items",
                    "localField": "item_id",
                    "foreignField": "_id",
                    "as": "item"
                }
            },
            { "$unwind": "$item" },
            { "$project": { "item": 1, "_id": 0 } },
            { "$replaceRoot": { "newRoot": "$item" } }
        ]))
        return liked_items

    def create_liked_item(self, item_id, user_id):
        item_object_id = ObjectId(item_id)
        user_object_id = ObjectId(user_id)
        current_time = datetime.utcnow()
        result = self.liked_items_collection.update_one(
            { "item_id": item_object_id, "user_id": user_object_id },
            { "$setOnInsert": { "item_id": item_object_id, "user_id": user_object_id, "date_liked": current_time } },
            upsert=True
        )
        return "Item already liked" if result.matched_count > 0 else "Item was liked"

    def delete_liked_item(self, item_id, user_id):
        item_object_id = ObjectId(item_id)
        user_object_id = ObjectId(user_id)
        self.liked_items_collection.delete_one({ "item_id": item_object_id, "user_id": user_object_id })
        return "Sucessfully unliked item"

    def get_wishlist_items(self, user_id):
        user_object_id = ObjectId(user_id)
        wishlist_items = list(self.wishlist_items_collection.aggregate([
            { "$match": { "user_id": user_object_id } },
            {
                "$lookup": {
                    "from": "items",
                    "localField": "item_id",
                    "foreignField": "_id",
                    "as": "item"
                }
            },
            { "$unwind": "$item" },
            { "$project": { "item": 1, "_id": 0 } },
            { "$replaceRoot": { "newRoot": "$item" } }
        ]))
        return wishlist_items

    def create_wishlist_item(self, item_id, user_id):
        item_object_id = ObjectId(item_id)
        user_object_id = ObjectId(user_id)
        current_time = datetime.utcnow()
        result = self.wishlist_items_collection.update_one(
            { "item_id": item_object_id, "user_id": user_object_id },
            { "$setOnInsert": { "item_id": item_object_id, "user_id": user_object_id, "date_liked": current_time } },
            upsert=True
        )
        return "Item already in wishlist" if result.matched_count > 0 else "Item was added to wishlist"

    def delete_wishlist_item(self, item_id, user_id):
        item_object_id = ObjectId(item_id)
        user_object_id = ObjectId(user_id)
        self.wishlist_items_collection.delete_one({ "item_id": item_object_id, "user_id": user_object_id })
        return "Sucessfully removed item from wishlist"
