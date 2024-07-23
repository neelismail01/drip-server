from bson import ObjectId
from datetime import datetime

class ClosetsManager:
    def __init__(self, mongo_client):
        self.db = mongo_client["drip"]
        self.items_collection = self.db["items"]
        self.closets_collection = self.db["closets"]

    def create_closet(self, name, user_id):
        user_object_id = ObjectId(user_id)
        existing_closet = self.closets_collection.find_one({ 'user_id': user_object_id, 'name': name })
        current_time = datetime.utcnow()
        if not existing_closet:
            new_closet = self.closets_collection.insert_one({
                'date_created': current_time,
                'name': name,
                'user_id': user_object_id,
                'products': [],
            })
            return "Closet was created" if new_closet else "Error creating closet"
        return "Closet already exists"

    def delete_closet(self, name, user_id):
        user_object_id = ObjectId(user_id)
        self.closets_collection.delete_one({ "user_id": user_object_id, "name": name })
        return "Sucessfully deleted closet"

    def get_closets_by_user(self, user_id):
        user_object_id = ObjectId(user_id)
        closets = list(self.closets_collection.find({'user_id': user_object_id}))

        for closet in closets:
            product_ids = closet['products']
            if len(product_ids) > 3:
                closet['cover_photo_products'] = list(
                    self.items_collection.find({'_id': {'$in': product_ids}}).sort('date_created', -1).limit(4)
                )
            elif 0 < len(product_ids) <= 3:
                closet['cover_photo_products'] = list(
                    self.items_collection.find({'_id': {'$in': product_ids}}).sort('date_created', -1).limit(1)
                )

        return closets

    def get_items_by_closet(self, user_id, closet_name):
        user_object_id = ObjectId(user_id)
        closet = self.closets_collection.find_one({
            'user_id': user_object_id,
            'name': closet_name
        })

        if closet:
            product_ids = closet['products']
            items = list(self.items_collection.find({'_id': {'$in': product_ids}}).sort('date_created', -1))
            return items

        return []

    def edit_closet_memberships(self, closets, user_id, product_id):
        product_object_id = ObjectId(product_id)
        user_object_id = ObjectId(user_id)
        results = []

        # Retrieve all closets for the user
        user_closets = self.closets_collection.find({'user_id': user_object_id})
        closet_ids_to_include = {ObjectId(closet['_id']) for closet in closets}

        for closet in user_closets:
            closet_id = closet['_id']
            if closet_id in closet_ids_to_include:
                # Add product_id to closets in the provided list if not already present
                if product_object_id not in closet['products']:
                    result = self.closets_collection.update_one(
                        {'_id': closet_id},
                        {'$addToSet': {'products': product_object_id}}
                    )
                    if result.modified_count > 0:
                        results.append(f"Item added to closet '{closet['name']}'")
                    else:
                        results.append(f"Item already in closet '{closet['name']}'")
                else:
                    results.append(f"Item already in closet '{closet['name']}'")
            else:
                # Remove product_id from closets not in the provided list
                if product_object_id in closet['products']:
                    result = self.closets_collection.update_one(
                        {'_id': closet_id},
                        {'$pull': {'products': product_object_id}}
                    )
                    if result.modified_count > 0:
                        results.append(f"Item removed from closet '{closet['name']}'")
                    else:
                        results.append(f"Item was not in closet '{closet['name']}'")
        return results