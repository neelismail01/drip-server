from bson import ObjectId
from datetime import datetime

class WishlistsManager:
    def __init__(self, mongo_client):
        self.db = mongo_client["drip"]
        self.items_collection = self.db["items"]
        self.outfits_collection = self.db["outfits"]
        self.closets_collection = self.db["closets"]
        self.wishlists_collection = self.db["wishlists"]

    def create_wishlist(self, name, user_id):
        user_object_id = ObjectId(user_id)
        existing_wishlist = self.wishlists_collection.find_one({ 'user_id': user_object_id, 'name': name })
        current_time = datetime.utcnow()
        if not existing_wishlist:
            new_wishlist = self.wishlists_collection.insert_one({
                'date_created': current_time,
                'name': name,
                'user_id': user_object_id,
                'products': [],
            })
            return "Wish List was created" if new_closet else "Error creating wish list"
        return "Wish List already exists"

    def delete_wishlist(self, name, user_id):
        user_object_id = ObjectId(user_id)
        self.wishlists_collection.delete_one({ "user_id": user_object_id, "name": name })
        return "Sucessfully deleted wish list"

    def get_wishlists_by_user(self, user_id):
        user_object_id = ObjectId(user_id)
        wishlists = list(self.wishlists_collection.find({'user_id': user_object_id}))

        for wishlist in wishlists:
            product_entries = wishlist['products']
            
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
                wishlist['cover_photo_products'] = all_products[:4]
            elif 0 < len(all_products) <= 3:
                wishlist['cover_photo_products'] = all_products[:1]

        return wishlists


    def get_products_by_wishlist(self, user_id, wishlist_name):
        user_object_id = ObjectId(user_id)
        wishlist = self.wishlists_collection.find_one({
            'user_id': user_object_id,
            'name': wishlist_name
        })

        if wishlist:
            product_entries = wishlist['products']
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

    def edit_wishlist_memberships(self, wishlists, user_id, product_id, product_type):
        product_object_id = ObjectId(product_id)
        user_object_id = ObjectId(user_id)
        results = []

        # Get posted by id
        if (product_type == "item"):
            full_product = self.items_collection.find_one({'_id': product_object_id})
        else:
            full_product = self.outfits_collection.find_one({'_id': product_object_id})
        posted_by_user_id = full_product['user_id']

        # Retrieve all wish lists for the user
        user_wishlists = self.wishlists_collection.find({'user_id': user_object_id})
        wishlists_ids_to_include = {ObjectId(wishlist['_id']) for wishlist in wishlists}

        for wishlist in user_wishlists:
            wishlist_id = wishlist['_id']
            existing_products_ids = [product['id'] for product in wishlist['products']]
            if wishlist_id in wishlists_ids_to_include:
                # Add product_id to wishlists in the provided list if not already present
                if product_object_id not in existing_products_ids:
                    current_time = datetime.utcnow()
                    result = self.wishlists_collection.update_one(
                        {'_id': wishlist_id},
                        {'$addToSet': {
                            'products': {
                                'type': product_type, 
                                'id': product_object_id,
                                'date_added': current_time,
                                'posted_by': posted_by_user_id
                            }
                        }}
                    )
                    if result.modified_count > 0:
                        results.append(f"Product added to wish list '{wishlist['name']}'")
                    else:
                        results.append(f"Product already in wish list '{wishlist['name']}'")
                else:
                    results.append(f"Product already in wish list '{wishlist['name']}'")
            else:
                # Remove product_id from wish lists not in the provided list
                if product_object_id in existing_products_ids:
                    result = self.wishlists_collection.update_one(
                        {'_id': wishlist_id},
                        {'$pull': {'products': {'type': product_type, 'id': product_object_id}}}
                    )
                    if result.modified_count > 0:
                        results.append(f"Product removed from wish list '{wishlist['name']}'")
                    else:
                        results.append(f"Product was not in wish list '{wishlist['name']}'")
        return results