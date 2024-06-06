class WishlistOutfit:
    def __init__(self, outfit_id, user_id):
        self.outfit_id = outfit_id
        self.user_id = user_id

    def to_dict(self):
        return {
            "outfit_id": self.outfit_id,
            "user_id": self.user_id,
        }

    @staticmethod
    def from_dict(data):
        return WishlistOutfit(
            outfit_id=data.get('outfit_id'),
            user_id=data.get('user_id'),
        )