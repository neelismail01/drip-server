class Outfit:
    def __init__(self, user_id, name, caption, items=[], tags=[], images=[]):
        self.user_id = user_id
        self.name = name
        self.caption = caption
        self.items = items,
        self.tags = tags
        self.images = images

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "caption": self.caption,
            "items": self.items,
            "tags": self.tags,
            "images": self.images,
        }

    @staticmethod
    def from_dict(data):
        return Outfit(
            user_id=data.get('user_id'),
            name=data.get('name'),
            caption=data.get('caption'),
            items=data.get('items'),
            tags=data.get('tags'),
            images=data.get('images'),
        )