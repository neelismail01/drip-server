class SocialGraphNode:
    def __init__(self, follower_id, follower_name, follower_username, followee_id, followee_name, followee_username, status):
        self.follower_id = follower_id
        self.follower_name = follower_name
        self.follower_username = follower_username
        self.followee_id = followee_id
        self.followee_name = followee_name
        self.followee_username = followee_username
        self.status = status

    def to_dict(self):
        return {
            "follower_id": self.follower_id,
            "follower_name": self.follower_name,
            "follower_username": self.follower_username,
            "followee_id": self.followee_id,
            "followee_name": self.followee_name,
            "followee_username": self.followee_username,
            "status": self.status
        }

    @staticmethod
    def from_dict(data):
        return SocialGraphNode(
            follower_id=data.get('follower_id'),
            follower_name=data.get('follower_name'),
            follower_username=data.get('follower_username'),
            followee_id=data.get('followee_id'),
            followee_name=data.get('followee_name'),
            followee_username=data.get('followee_username'),
            status=data.get('status')
        )