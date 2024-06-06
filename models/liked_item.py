class LikedItem:
    def __init__(self, item_id, user_id):
        self.item_id = item_id
        self.user_id = user_id

    def to_dict(self):
        return {
            "item_id": self.item_id,
            "user_id": self.user_id,
        }

    @staticmethod
    def from_dict(data):
        return LikedItem(
            item_id=data.get('item_id'),
            user_id=data.get('user_id'),
        )