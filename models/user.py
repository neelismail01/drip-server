from flask_login import UserMixin

class User(UserMixin):
    @staticmethod
    def get(user_id):
        pass

    @staticmethod
    def create(user_id, name, email):
        pass
