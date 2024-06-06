class Item:
    def __init__(self, brand, item_name, gender, images, product_page_link="", tags=[]):
        self.brand = brand
        self.item_name = item_name
        self.gender = gender,
        self.images = images
        self.product_page_link = product_page_link
        self.tags = tags

    def to_dict(self):
        return {
            "brand": self.brand,
            "item_name": self.item_name,
            "gender": self.gender,
            "images": self.images,
            "product_page_link": self.product_page_link,
            "tags": self.tags,
        }

    @staticmethod
    def from_dict(data):
        return Item(
            brand=data.get('brand'),
            item_name=data.get('item_name'),
            gender=data.get('gender'),
            images=data.get('images'),
            product_page_link=data.get('product_page_link'),
            tags=data.get('tags'),
        )