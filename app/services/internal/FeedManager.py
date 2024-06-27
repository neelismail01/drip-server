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

    def get_all_items(self, filter={}, skip=0, limit=0):
        items = list(self.items_collection.aggregate([
            { "$match": filter },
            { "$skip": skip },
            { "$limit": limit }
        ]))
        for item in items:
            item["productType"] = "item"
        return items

    def get_all_outfits(self, filter={}, skip=0, limit=0):
        outfits = list(self.outfits_collection.aggregate([
            { "$match": filter },
            {
                "$lookup": {
                    "from": "items",
                    "localField": "items",
                    "foreignField": "_id",
                    "as": "items"
                }
            },
            { "$skip": skip },
            { "$limit": limit }
        ]))
        for outfit in outfits:
            outfit["productType"] = "outfit"
        return outfits

    def get_user_following(self, user_id):
        following = list(self.social_graph_collection.find({"follower_id": ObjectId(user_id)}))
        return [str(user["followee_id"]) for user in following]

    def get_items_by_users(self, user_ids, skip=0, limit=0):
        filter = {"user_id": {"$in": user_ids}}
        return self.get_all_items(filter, skip, limit)

    def get_outfits_by_users(self, user_ids, skip=0, limit=0):
        filter = {"user_id": {"$in": user_ids}}
        return self.get_all_outfits(filter, skip, limit)

    def get_liked_or_wishlist_items_by_users(self, user_ids, collection):
        liked_items = list(collection.find({"user_id": {"$in": user_ids}}))
        item_ids = [item["item_id"] for item in liked_items]
        return list(self.items_collection.find({"_id": {"$in": item_ids}}))

    def get_liked_or_wishlist_outfits_by_users(self, user_ids, collection):
        liked_outfits = list(collection.find({"user_id": {"$in": user_ids}}))
        outfit_ids = [outfit["outfit_id"] for outfit in liked_outfits]
        return list(self.outfits_collection.find({"_id": {"$in": outfit_ids}}))

    def get_all_products(self, user_id, page, page_size):
        skip = (page - 1) * page_size
        
        following = self.get_user_following(user_id)
        
        items_by_following = self.get_items_by_users(following, skip, page_size)
        outfits_by_following = self.get_outfits_by_users(following, skip, page_size)
        
        liked_items_by_following = self.get_liked_or_wishlist_items_by_users(following, self.liked_items_collection)
        wishlist_items_by_following = self.get_liked_or_wishlist_items_by_users(following, self.wishlist_items_collection)
        
        liked_outfits_by_following = self.get_liked_or_wishlist_outfits_by_users(following, self.liked_outfits_collection)
        wishlist_outfits_by_following = self.get_liked_or_wishlist_outfits_by_users(following, self.wishlist_outfits_collection)
        
        remaining_items = self.get_all_items({}, skip, page_size)
        remaining_outfits = self.get_all_outfits({}, skip, page_size)
        
        combined_products = items_by_following + outfits_by_following + \
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