from bson import ObjectId

class FeedManager:
    def __init__(self, mongo_client):
        self.db = mongo_client["drip"]
        self.items_collection = self.db["items"]
        self.outfits_collection = self.db["outfits"]
        self.social_graph_collection = self.db["social_graph"]
        self.liked_items_collection = self.db["liked_items"]
        self.wishlist_items_collection = self.db["wishlist_items"]
        self.liked_outfits_collection = self.db["liked_outfits"]
        self.wishlist_outfits_collection = self.db["wishlist_outfits"]

    def get_all_items(self, filter={}):
        items = list(self.items_collection.aggregate([
            { "$match": filter }
        ]))
        for item in items:
            item["productType"] = "item"
        return items

    def get_all_outfits(self, filter={}):
        outfits = list(self.outfits_collection.aggregate([
            { "$match": filter },
            {
                "$lookup": {
                    "from": "items",
                    "localField": "items",
                    "foreignField": "_id",
                    "as": "items"
                }
            }
        ]))
        for outfit in outfits:
            outfit["productType"] = "outfit"
        return outfits

    def get_user_following(self, user_id):
        following = list(self.social_graph_collection.find({"follower_id": ObjectId(user_id), "followee_type": "user"}))
        return [str(user["followee_id"]) for user in following]

    def get_items_by_users(self, user_ids):
        filter = {"user_id": {"$in": user_ids}}
        return self.get_all_items(filter)

    def get_outfits_by_users(self, user_ids):
        filter = {"user_id": {"$in": user_ids}}
        return self.get_all_outfits(filter)

    def get_liked_items_by_users(self, user_ids, collection):
        liked_items = list(collection.find({"liked_by": {"$in": user_ids}}))
        item_ids = [item["post_id"] for item in liked_items]
        return list(self.items_collection.find({"_id": {"$in": item_ids}}))

    def get_wishlist_items_by_users(self, user_ids, collection):
        added_items = list(collection.find({"added_by": {"$in": user_ids}}))
        item_ids = [item["post_id"] for item in added_items]
        return list(self.items_collection.find({"_id": {"$in": item_ids}}))

    def get_liked_outfits_by_users(self, user_ids, collection):
        liked_outfits = list(collection.find({"liked_by": {"$in": user_ids}}))
        outfit_ids = [outfit["post_id"] for outfit in liked_outfits]
        return list(self.outfits_collection.find({"_id": {"$in": outfit_ids}}))

    def get_wishlist_outfits_by_users(self, user_ids, collection):
        added_outfits = list(collection.find({"added_by": {"$in": user_ids}}))
        outfit_ids = [outfit["post_id"] for outfit in added_outfits]
        return list(self.outfits_collection.find({"_id": {"$in": outfit_ids}}))

    def get_items_by_brands(self, brand_ids):
        filter = {"brand_id": {"$in": brand_ids}}
        return self.get_all_items(filter)

    def get_user_followed_brands(self, user_id):
        followed_brands = list(self.social_graph_collection.find({"follower_id": ObjectId(user_id), "followee_type": "brand"}))
        return [str(brand["followee_id"]) for brand in followed_brands]

    def get_all_products(self, user_id, page, page_size):
        skip = (page - 1) * page_size
        
        following_users = self.get_user_following(user_id)
        followed_brands = self.get_user_followed_brands(user_id)
        
        items_by_following = self.get_items_by_users(following_users)
        outfits_by_following = self.get_outfits_by_users(following_users)
        
        liked_items_by_following = self.get_liked_items_by_users(following_users, self.liked_items_collection)
        wishlist_items_by_following = self.get_wishlist_items_by_users(following_users, self.wishlist_items_collection)
        
        liked_outfits_by_following = self.get_liked_outfits_by_users(following_users, self.liked_items_collection)
        wishlist_outfits_by_following = self.get_wishlist_outfits_by_users(following_users, self.wishlist_items_collection)
        
        items_by_brands = self.get_items_by_brands(followed_brands)
        
        remaining_items = self.get_all_items()
        remaining_outfits = self.get_all_outfits()
        
        combined_products = items_by_following + outfits_by_following + \
                            items_by_brands + \
                            liked_items_by_following + wishlist_items_by_following + \
                            liked_outfits_by_following + wishlist_outfits_by_following + \
                            remaining_items + remaining_outfits
        
        # Remove duplicates
        seen = set()
        unique_products = []
        for product in combined_products:
            if product["_id"] not in seen:
                unique_products.append(product)
                seen.add(product["_id"])
        
        # Sort by date_created
        unique_products.sort(key=lambda x: x["date_created"], reverse=True)
        
        # Pagination
        paginated_products = unique_products[skip:skip + page_size]
        
        return paginated_products