import json
from flask import (
    current_app,
    Blueprint,
    request
)
from app.utils.constants.llm_prompts import (
    ASSISTANT_IMAGE_GENERATION_PROMPT,
    ASSISTANT_MISUSE_PROMPT,
    ASSISTANT_MISUSE_RESPONSE,
    ASSISTANT_OUTFIT_ITEM_EXTRACTION_PROMPT,
)
from app.utils.MongoJsonEncoder import MongoJSONEncoder

assistant_blueprint = Blueprint('assistant', __name__)
    
@assistant_blueprint.route('/chats/<user_id>', methods=["GET"])
def get_all_chats(user_id):
    chats = current_app.assistant_chat_manager.get_all_chats(user_id)
    return json.dumps(chats, cls=MongoJSONEncoder)

@assistant_blueprint.route('/chat/<chat_id>', methods=["GET"])
def get_chat(chat_id):
    chat = current_app.assistant_chat_manager.get_chat(chat_id)
    return json.dumps(chat, cls=MongoJSONEncoder)

def evaluate_user_message_for_misuse(message):
    chat_preamble = [
        { "role": "system", "content" : ASSISTANT_MISUSE_PROMPT },
        { "role": "user", "content": message }
    ]
    chat_response = current_app.groq_manager.get_chat_response(chat_preamble, 1)
    misuse = True if chat_response == "no" else False
    return misuse

def get_chat_response(chat_history):
    most_recent_message = chat_history[-1]["text"]
    misuse = evaluate_user_message_for_misuse(most_recent_message)
    if misuse:
        return ASSISTANT_MISUSE_RESPONSE
    text_messages = list(filter(lambda item: item["content_type"] == "text", chat_history))
    groq_messages = list(map(lambda item: { "role": item["role"], "content": item["text"] }, text_messages))
    chat_response = current_app.groq_manager.get_chat_response(groq_messages, 512)
    return chat_response

@assistant_blueprint.route('/chat/<user_id>', methods=["POST"])
def create_chat(user_id):
    data = request.json
    chat_history = data.get("chatHistory")
    chat_response = get_chat_response(chat_history)
    chat_history.append({
        "id": str(len(chat_history) + 1),
        "role": "assistant",
        "text": chat_response,
        "content_type": "text"
    })
    chat_id = current_app.assistant_chat_manager.create_chat(user_id, chat_history)
    return json.dumps({  "chat_response": chat_response, "chat_id": chat_id }, cls=MongoJSONEncoder)

@assistant_blueprint.route('/chat/<chat_id>', methods=["PUT"])
def update_chat(chat_id):
    data = request.json
    chat_history = data.get("chatHistory")
    chat_response = get_chat_response(chat_history)
    chat_history.append({
        "id": str(len(chat_history) + 1),
        "role": "assistant",
        "text": chat_response,
        "content_type": "text"
    })
    new_messages = chat_history[-2:]
    current_app.assistant_chat_manager.update_chat(chat_id, new_messages)
    return json.dumps({ "chat_response": chat_response }, cls=MongoJSONEncoder)

@assistant_blueprint.route('/image/<chat_id>', methods=["POST"])
def create_outfit_image(chat_id):
    data = request.json
    prompt = data.get("prompt")
    chat_history = data.get("chatHistory")
    full_prompt = ASSISTANT_IMAGE_GENERATION_PROMPT + prompt
    image_url = current_app.dalle_manager.get_generated_image(full_prompt)
    new_messages = [{
        "id": str(len(chat_history) + 1),
        "role": "assistant",
        "image": image_url,
        "content_type": "image"
    }]
    current_app.assistant_chat_manager.update_chat(chat_id, new_messages)
    return json.dumps({ "image_url": image_url }, cls=MongoJSONEncoder)

def extract_items_from_outfit_description(outfit_description):
    chat_preamble = [
        { "role": "system", "content": ASSISTANT_OUTFIT_ITEM_EXTRACTION_PROMPT },
        { "role": "user", "content": outfit_description }
    ]
    extracted_items = current_app.groq_manager.get_chat_response(chat_preamble, 512)
    return json.loads(extracted_items)

@assistant_blueprint.route('/search/<chat_id>', methods=["POST"])
def search_items(chat_id):
    data = request.json
    outfit_description = data.get("outfitDescription")
    chat_history = data.get("chatHistory")
    extracted_items = extract_items_from_outfit_description(outfit_description)
    relevant_items = current_app.assistant_chat_manager.search_for_relevant_items(extracted_items)
    new_messages = [{
        "id": str(len(chat_history) + 1),
        "role": "assistant",
        "relevant_items": relevant_items,
        "content_type": "relevant_items"
    }]
    current_app.assistant_chat_manager.update_chat(chat_id, new_messages)
    return json.dumps({ "relevant_items": relevant_items }, cls=MongoJSONEncoder)
