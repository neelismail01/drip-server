class AssistantChat:
    def __init__(self, user_id, date_created, date_updated, title, messages):
        self.user_id = user_id
        self.date_created = date_created
        self.date_updated = date_updated
        self.title = title
        self.messages = [Message.from_dict(msg) if isinstance(msg, dict) else msg for msg in messages]

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "date_created": self.date_created,
            "date_updated": self.date_updated,
            "title": self.title,
            "messages": [msg.to_dict() for msg in self.messages]
        }

    @staticmethod
    def from_dict(data):
        return AssistantChat(
            user_id=data.get('user_id'),
            date_created=data.get('date_created'),
            date_updated=data.get('date_updated'),
            title=data.get('title'),
            messages=[Message.from_dict(msg) for msg in data.get('messages', [])]
        )

class Message:
    def __init__(self, id, role, content_type, text=None, image=None, relevant_items=None):
        self.id = id
        self.role = role
        self.content_type = content_type
        self.text = text
        self.image = image
        self.relevant_items = relevant_items

    def to_dict(self):
        return {
            "id": self.id,
            "role": self.role,
            "content_type": self.content_type,
            "text": self.text,
            "image": self.image,
            "relevant_items": self.relevant_items
        }

    @staticmethod
    def from_dict(data):
        return Message(
            id=data.get('id'),
            role=data.get('role'),
            content_type=data.get('content_type'),
            text=data.get('text'),
            image=data.get('image'),
            relevant_items=data.get('relevant_items')
        )
