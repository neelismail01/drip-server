from flask import (
    current_app,
    Blueprint,
    jsonify,
    request
)
import os
import datetime
from bson import ObjectId
from groq import Groq
from openai import OpenAI

assistant_blueprint = Blueprint('assistant', __name__)

groq_client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)
openai_client = OpenAI()


@assistant_blueprint.route('/chat/<chat_id>', methods=["GET"])
def get_chat(chat_id):
    db = current_app.mongo.drip
    try:
        # Convert user_id to ObjectId if necessary
        # If user_id is not an ObjectId, remove the next line
        chat_object_id = ObjectId(chat_id)
    except Exception as e:
        return jsonify({"error": "Invalid user ID"}), 400

    # Find all documents matching the user_id
    chats = list(db.assistant_chats.find({'_id': chat_object_id}))

    if len(chats) > 0:
        return jsonify({'messages': chats[0]['messages']}), 200
    
    return jsonify({"error": "Chat ID does not exist"}), 400

@assistant_blueprint.route('/chats/<user_id>', methods=["GET"])
def get_all_chats(user_id):
    db = current_app.mongo.drip
    try:
        # Convert user_id to ObjectId if necessary
        # If user_id is not an ObjectId, remove the next line
        user_object_id = ObjectId(user_id)
    except Exception as e:
        return jsonify({"error": "Invalid user ID"}), 400

    # Find all documents matching the user_id
    chats = list(db.assistant_chats.find({'user_id': user_object_id}).sort('date_updated', -1))

    # Convert ObjectId to string for JSON serialization
    for chat in chats:
        chat['_id'] = str(chat['_id'])
        chat['user_id'] = str(chat['user_id'])

    return jsonify({'chats': chats}), 200

def evaluate_chat_request_for_misuse(message):
    chat_preamble = [
        {
            "role": "system",
            "content" : "you are an assistant evaluating whether the topic of a provided message is related to fashion. is the following message related to fashion? answer yes or no."
        },
        {
            "role": "user",
            "content": message
        }
    ]

    chat_completion = groq_client.chat.completions.create(
        messages=chat_preamble,
        model="llama3-8b-8192",
        temperature=0,
        max_tokens=1,
        top_p=1
    )

    response_content = chat_completion.choices[0].message.content.lower()
    misuse = True if response_content == "no" else False
    return misuse

def get_chat_response(chat_history):
    most_recent_message = chat_history[-1]["content"]
    misuse = evaluate_chat_request_for_misuse(most_recent_message)
    if misuse:
        return "As a fashion assistant, I cannot answer this question."

    text_messages = list(filter(lambda item: item["content_type"] == "text", chat_history))
    messages = list(map(lambda item: { "role": item['role'], "content": item['content'] }, text_messages))
    chat_completion = groq_client.chat.completions.create(
        messages=messages,
        model="llama3-8b-8192",
        temperature=1,
        max_tokens=512,
        top_p=1
    )

    chat_response = chat_completion.choices[0].message.content
    return chat_response

@assistant_blueprint.route('/chat/<user_id>', methods=["POST"])
def create_chat(user_id):
    try:
        user_object_id = ObjectId(user_id)
    except Exception as e:
        return jsonify({"error": "Invalid user ID"}), 400

    db = current_app.mongo.drip
    data = request.json
    chat_history = data.get("chatHistory")

    chat_response = get_chat_response(chat_history)
    chat_history.append({
        "id": str(len(chat_history) + 1),
        "role": "assistant",
        "content": chat_response,
        "content_type": "text"
    })

    current_time = datetime.datetime.utcnow()
    title = chat_history[2]["content"] if len(chat_history[2]["content"]) < 50 else chat_history[2]["content"][:50] + "..."
    result = db.assistant_chats.insert_one({
        "user_id": user_object_id,
        "messages": chat_history,
        "date_created": current_time,
        "date_updated": current_time,
        "title": title
    })

    document_id = str(result.inserted_id)
    return { "chat_response": chat_response, "chat_id": document_id }, 200

@assistant_blueprint.route('/chat/<chat_id>', methods=["PUT"])
def update_chat(chat_id):
    try:
        chat_object_id = ObjectId(chat_id)
    except Exception as e:
        return jsonify({"error": "Invalid chat ID"}), 400

    db = current_app.mongo.drip
    data = request.json
    chat_history = data.get("chatHistory")

    chat_response = get_chat_response(chat_history)
    chat_history.append({
        "id": str(len(chat_history) + 1),
        "role": "assistant",
        "content": chat_response,
        "content_type": "text"
    })
    new_messages = chat_history[-2:]

    current_time = datetime.datetime.utcnow()
    db.assistant_chats.update_one(
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

    return { "chat_response": chat_response }, 200

@assistant_blueprint.route('/image/<chat_id>', methods=["POST"])
def create_outfit_image(chat_id):
    try:
        chat_object_id = ObjectId(chat_id)
    except Exception as e:
        return jsonify({"error": "Invalid chat ID"}), 400

    prompt_preamble = """Create a picture that only consists of a single mannequin wearing all 
    items in the outfit described below. The background should be a chic hardwood floored 
    fitting room. The whole body of the mannequin should be shown. """

    db = current_app.mongo.drip
    data = request.json
    prompt = data.get("prompt")
    chat_history = data.get("chatHistory")

    full_prompt = prompt_preamble + prompt
    try:
        response = openai_client.images.generate(
            prompt=full_prompt,
            model="dall-e-3",
            n=1,
            size="1024x1024",
            style="vivid"
        ) 
        image_url = response.data[0].url

        new_message = {
            "id": str(len(chat_history) + 1),
            "role": "assistant",
            "content": image_url,
            "content_type": "image"
        }
        current_time = datetime.datetime.utcnow()
        db.assistant_chats.update_one(
            { "_id": chat_object_id },
            {
                "$push": {
                    "messages": new_message
                },
                "$set": {
                    "date_updated": current_time
                }
            }
        )

        return jsonify({"image_url": image_url}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 400