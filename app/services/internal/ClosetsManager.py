from bson import ObjectId
from datetime import datetime

class ClosetsManager:
    def __init__(self, mongo_client):
        self.db = mongo_client["drip"]
        self.items_collection = self.db["items"]
        self.outfits_collection = self.db["outfits"]
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
            product_entries = closet['products']
            
            items = []
            outfits = []
            all_products = []

            for entry in product_entries:
                product = None
                if entry['type'] == 'item':
                    product = self.items_collection.find_one({'_id': ObjectId(entry['id'])})
                elif entry['type'] == 'outfit':
                    product = self.outfits_collection.find_one({'_id': ObjectId(entry['id'])})
                
                if product:
                    product['date_added'] = entry['date_added']  # Include date_added field in the product
                    all_products.append(product)
                
                if len(all_products) >= 4:
                    break

            # Sort the combined list by date_added field
            all_products.sort(key=lambda x: x['date_added'], reverse=True)

            if len(all_products) > 3:
                closet['cover_photo_products'] = all_products[:4]
            elif 0 < len(all_products) <= 3:
                closet['cover_photo_products'] = all_products[:1]

        return closets

    def get_products_by_closet(self, user_id, closet_name):
        user_object_id = ObjectId(user_id)
        closet = self.closets_collection.find_one({
            'user_id': user_object_id,
            'name': closet_name
        })

        if closet:
            product_entries = closet['products']
            items = []
            outfits = []

            for entry in product_entries:
                if entry['type'] == 'item':
                    item = self.items_collection.find_one({'_id': ObjectId(entry['id'])})
                    if item:
                        items.append(item)
                elif entry['type'] == 'outfit':
                    outfit = self.outfits_collection.find_one({'_id': ObjectId(entry['id'])})
                    if outfit:
                        outfit_items = [self.items_collection.find_one({'_id': item_id}) for item_id in outfit['items']]
                        outfit['items'] = [item for item in outfit_items if item]  # Filter out None values
                        outfits.append(outfit)

            all_products = items + outfits
            all_products.sort(key=lambda x: x['date_created'], reverse=True)

            return all_products

        return []

    def edit_closet_memberships(self, closets, user_id, product_id, product_type):
        product_object_id = ObjectId(product_id)
        user_object_id = ObjectId(user_id)
        results = []

        # Retrieve all closets for the user
        user_closets = self.closets_collection.find({'user_id': user_object_id})
        closet_ids_to_include = {ObjectId(closet['_id']) for closet in closets}

        for closet in user_closets:
            closet_id = closet['_id']
            existing_products_ids = [product['id'] for product in closet['products']]
            if closet_id in closet_ids_to_include:
                # Add product_id to closets in the provided list if not already present
                if product_object_id not in existing_products_ids:
                    current_time = datetime.utcnow()
                    result = self.closets_collection.update_one(
                        {'_id': closet_id},
                        {'$addToSet': {
                            'products': {
                                'type': product_type, 
                                'id': product_object_id,
                                'date_added': current_time,
                            }
                        }}
                    )
                    if result.modified_count > 0:
                        results.append(f"Product added to closet '{closet['name']}'")
                    else:
                        results.append(f"Product already in closet '{closet['name']}'")
                else:
                    results.append(f"Product already in closet '{closet['name']}'")
            else:
                # Remove product_id from closets not in the provided list
                if product_object_id in existing_products_ids:
                    result = self.closets_collection.update_one(
                        {'_id': closet_id},
                        {'$pull': {'products': {'type': product_type, 'id': product_object_id}}}
                    )
                    if result.modified_count > 0:
                        results.append(f"Product removed from closet '{closet['name']}'")
                    else:
                        results.append(f"Product was not in closet '{closet['name']}'")
        return results