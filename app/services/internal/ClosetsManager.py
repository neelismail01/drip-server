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

    def edit_closet_name(self, user_id, current_name, new_name):
        user_object_id = ObjectId(user_id)
        closet = self.closets_collection.find_one({
            'user_id': user_object_id,
            'name': current_name
        })

        # Check if a wishlist with the new name already exists
        existing_closet = self.closets_collection.find_one({
            'user_id': user_object_id,
            'name': new_name
        })
        if existing_closet:
            return {"error": "Closet with the new name already exists"}, 400

        # Update the closet name
        result = self.closets_collection.update_one(
            {'_id': closet['_id']},
            {'$set': {'name': new_name}}
        )

        if result.modified_count == 0:
            return {"error": "Failed to update closet name"}, 500

        return {"message": "Closet name updated successfully"}

    def remove_products_from_closet(self, user_id, closet_name, products):
        user_object_id = ObjectId(user_id)
        closet = self.closets_collection.find_one({
            'user_id': user_object_id,
            'name': closet_name
        })

        product_ids = [ObjectId(product['_id']) for product in products]

        result = self.closets_collection.update_one(
            {'_id': closet['_id']},
            {'$pull': {'products': {'id': {'$in': product_ids}}}}
        )

        if result.modified_count == 0:
            return {"error": "Failed to remove products from closet"}, 500

        return {"message": "Products removed from closet successfully"}

    def add_products_to_closet(self, user_id, closet_name, products):
        user_object_id = ObjectId(user_id)

        # Retrieve the specified closet
        closet = self.closets_collection.find_one({
            'user_id': user_object_id,
            'name': closet_name
        })

        if not closet:
            return {"error": "Closet not found"}, 404

        closet_id = closet['_id']
        current_time = datetime.utcnow()
        update_results = []

        for product in products:
            product_id = ObjectId(product['_id'])
            product_type = 'outfit' if 'items' in product else 'item'

            result = self.closets_collection.update_one(
                {'_id': closet_id},
                {'$addToSet': {
                    'products': {
                        'type': product_type,
                        'id': product_id,
                        'date_added': current_time
                    }
                }}
            )

            if result.modified_count > 0:
                update_results.append(f"Product added to closet '{closet_name}'")
            else:
                update_results.append(f"Product already in closet '{closet_name}'")

        return update_results

    def get_products_not_in_closet(self, user_id, closet_name):
        user_object_id = ObjectId(user_id)
        
        # Retrieve the specified closet
        closet = self.closets_collection.find_one({
            'user_id': user_object_id,
            'name': closet_name
        })

        # Get the IDs of products already in the closet
        existing_product_ids = {ObjectId(product['id']) for product in closet['products']}

        # Retrieve all items and outfits
        all_items = list(self.items_collection.find({ 'user_id': user_object_id }))
        all_outfits = list(self.outfits_collection.find({ 'user_id': user_object_id }))

        # Filter out items and outfits that are already in the closet
        items_not_in_closet = [item for item in all_items if item['_id'] not in existing_product_ids]
        outfits_not_in_closet = [outfit for outfit in all_outfits if outfit['_id'] not in existing_product_ids]

        # Combine items and outfits
        all_products_not_in_closet = items_not_in_closet + outfits_not_in_closet

        # Sort the combined list by date_created field
        all_products_not_in_closet.sort(key=lambda x: x['date_created'], reverse=True)

        return all_products_not_in_closet


