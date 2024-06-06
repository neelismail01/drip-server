class Brands:
    def __init__(self, brand_name, username, profile_pic, purchase_count=0, followers=[]):
        self.brand_name = brand_name
        self.username = username
        self.profile_pic = profile_pic
        self.purchase_count = purchase_count
        self.followers = followers

    def to_dict(self):
        return {
            "brand_name": self.brand_name,
            "username": self.username,
            "profile_pic": self.profile_pic,
            "purchase_count": self.purchase_count,
            "followers": self.followers,
        }

    @staticmethod
    def from_dict(data):
        return Brands(
            brand_name=data.get('brand_name'),
            username=data.get('username'),
            profile_pic=data.get('profile_pic'),
            purchase_count=data.get('purchase_count'),
            followers=data.get('followers'),
        )