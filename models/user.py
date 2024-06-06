class User:
    def __init__(self, name, username, email, preference, profile_complete, birthdate, profile_pic=None):
        self.name = name
        self.username = username
        self.email = email
        self.preference = preference,
        self.profile_complete = profile_complete
        self.birthdate = birthdate
        self.profile_pic = profile_pic

    def to_dict(self):
        return {
            "name": self.name,
            "username": self.username,
            "email": self.email,
            "preference": self.preference,
            "profile_complete": self.profile_complete,
            "birthdate": self.birthdate,
            "profile_pic": self.profile_pic
        }

    @staticmethod
    def from_dict(data):
        return User(
            name=data.get('name'),
            username=data.get('username'),
            email=data.get('email'),
            preference=data.get('preference'),
            profile_complete=data.get('profile_complete'),
            birthdate=data.get('birthdate'),
            profile_pic=data.get('profile_pic')
        )