from bson import ObjectId
from datetime import datetime

class AssistantChatManager:
    def __init__(self, mongo_client):
        self.db = mongo_client["drip"]
        self.assistant_chat_collection = self.db["assistant_chats"]
        self.items_collection = self.db["items"]

    def get_all_chats(self, user_id):
        user_object_id = ObjectId(user_id)
        chats = list(self.assistant_chat_collection.find({ 'user_id': user_object_id }).sort('date_updated', -1))
        return chats

    def get_chat(self, chat_id):
        chat_object_id = ObjectId(chat_id)
        chat = self.assistant_chat_collection.find_one({ '_id': chat_object_id })
        return chat

    def create_chat(self, user_id, chat_history):
        user_object_id = ObjectId(user_id)
        current_time = datetime.utcnow()
        first_user_message = chat_history[2]["text"]
        title = first_user_message if len(first_user_message) < 50 else first_user_message[:50] + "..."
        result = self.assistant_chat_collection.insert_one({
            "user_id": user_object_id,
            "messages": chat_history,
            "date_created": current_time,
            "date_updated": current_time,
            "title": title
        })
        document_id = str(result.inserted_id)
        return document_id

    def update_chat(self, chat_id, new_messages):
        chat_object_id = ObjectId(chat_id)
        current_time = datetime.utcnow()
        self.assistant_chat_collection.update_one(
             { "_id": chat_object_id },
             {
                "$push": {
                    "messages": {
                        "$each": new_messages
                    }
                },
                "$set": {
                    "date_updated": current_time
                }
            }
        )

    def search_for_relevant_items(self, extracted_items):
        def create_filter_query(clothing_items):
            return [{
                '$match': {
                    '$or': [
                        {
                            '$and': [
                                {'description': {'$regex': detail, '$options': 'i'}}
                                for detail in clothing_item.split(" ")
                            ]
                        }
                        for clothing_item in clothing_items
                    ]
                }
            }]

        relevant_items = self.items_collection.aggregate({
            '$facet': {
                'tops': create_filter_query(extracted_items["tops"]),
                'bottoms': create_filter_query(extracted_items["bottoms"]),
                'shoes': create_filter_query(extracted_items["shoes"]),
                'accessories': create_filter_query(extracted_items["accessories"]),
            }
        })
        return relevant_items
