import json
import pprint
from flask import (
    current_app,
    Blueprint,
    jsonify,
    request
)
import os
import datetime
from bson import ObjectId, json_util
from groq import Groq
from openai import OpenAI

assistant_blueprint = Blueprint('assistant', __name__)

groq_client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)
openai_client = OpenAI()

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

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

    if len(chats) == 0:
        return jsonify({"error": "Chat ID does not exist"}), 400
    
    return json.loads(json_util.dumps({'messages': chats[0]['messages']})), 200
    

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
    return json.loads(json_util.dumps({'chats': chats})), 200

def evaluate_chat_request_for_misuse(message):
    chat_preamble = [
        {
            "role": "system",
            "content" : (
                """
                you are an assistant evaluating whether the topic of a provided message is related to fashion. 
                is the following message related to fashion? answer yes or no.
                """
            )
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

def classify_user_message_intent(query):
    prompt_text = (
        """
        You’re a LLM that detects intent from user queries. Your task is to classify the user's intent based on their query. Below are 4 possible intents with brief descriptions. Use these to accurately determine the user's goal. Please only output the intent topic.

        - Advice For Occasion: Inquiries about what to wear for a specific occasion. An example of this kind of query would be "What should I wear for a job interview at law firm?".

        - Build Around Item: Inquiries about how to build an outfit using one or multiple items defined in the query. An example of this kind of query would be "I have a white linen shirt. Can you recommend an outfit I can build around this clothing item?".

        - Other: Choose this if the query doesn’t fall into any of the other intents.
        """
    )

    chat_preamble = [
        {
            "role": "system",
            "content" : prompt_text
        },
        {
            "role": "user",
            "content": query
        }
    ]

    chat_completion = groq_client.chat.completions.create(
        messages=chat_preamble,
        model="llama3-8b-8192",
        temperature=0,
        max_tokens=128,
        top_p=1
    )
    user_intent = chat_completion.choices[0].message.content
    return user_intent

def get_chat_response(chat_history):
    most_recent_message = chat_history[-1]["text"]
    misuse = evaluate_chat_request_for_misuse(most_recent_message)
    if misuse:
        return "As a fashion assistant, I cannot answer this question."

    user_intent = classify_user_message_intent(most_recent_message)
    text_messages = list(filter(lambda item: item["content_type"] == "text", chat_history))
    messages = list(map(lambda item: { "role": item["role"], "content": item["text"] }, text_messages))
    messages_with_prompting = messages
    match user_intent:
        case "Advice For Occasion":
            messages_with_prompting[-1]["content"] = (
                """
                You are providing advice for what someone should wear to an occasion described below.
                Please provide a single outfit recommendation. Please format the output with bullets describing 
                what the top, bottoms, shoes, and accessories should look like, respectively. Describe the outfit
                as simply as possible. \n
                """
            ) + most_recent_message
        case "Other":
            pass

    chat_completion = groq_client.chat.completions.create(
        messages=messages_with_prompting,
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
        "text": chat_response,
        "content_type": "text"
    })

    current_time = datetime.datetime.utcnow()
    title = (
        chat_history[2]["text"] 
        if len(chat_history[2]["text"]) < 50 
        else chat_history[2]["text"][:50] + "..."
    )
    result = db.assistant_chats.insert_one({
        "user_id": user_object_id,
        "messages": chat_history,
        "date_created": current_time,
        "date_updated": current_time,
        "title": title
    })

    document_id = str(result.inserted_id)

    return (json.loads(json_util.dumps({ 
        "chat_response": chat_response, 
        "chat_id": document_id, 
    })), 200)

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
        "text": chat_response,
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

    return (json.loads(json_util.dumps({"chat_response": chat_response })), 200)

@assistant_blueprint.route('/image/<chat_id>', methods=["POST"])
def create_outfit_image(chat_id):
    try:
        chat_object_id = ObjectId(chat_id)
    except Exception as e:
        return jsonify({"error": "Invalid chat ID"}), 400

    prompt_preamble = (
        """
        You will be given a description of an outfit. Please create a picture that consists of a 
        single mannequin wearing all items in the described outfit. The background should be a chic 
        hardwood floored fitting room. The whole body of the mannequin should be shown. If multiple 
        colours are proposed for a particular clothing item, use the first colour in your depiction.

        Outfit description: \n\n
        """
    )

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
            "image": image_url,
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

        return (json.loads(json_util.dumps({"image_url": image_url})), 200)
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 400

def extract_items_from_outfit_description(outfit_description):
    prompt_text = (
        """
        You are an LLM that analyzes an outfit description and identifies fashion items along with their 
        corresponding colors. Your task is to extract all individual items in the described 
        outfit organized by tops, bottoms, shoes, and accessories. If an item is described with multiple
        possible colors, produce separate entries in the output. Disregard any descriptive words that aren't 
        related to the name of the fashion item or its color. Here is an example of an input and output for 
        this task. Only produce the JSON in the output.

        Input:
        - Top: Light blue dress shirt with a slim collar and comfortable fit.
        - Bottoms: Dark gray or black slim-fit trousers or chinos for a sharp, yet relaxed look.
        - Shoes: Black or brown leather dress shoes, polished to perfection.
        - Accessories: Simple leather belt, slim watch, and a simple silver or leather cufflink.

        Output:
        {
            "tops": ["white sweater", "light blue sweater", "blush-colored dress shirt"],
            "bottoms": ["dark-washed jeans", "dark gray jeans", "dark gray chinos"],
            "shoes": ["black leather shoes", "loafers"]
            "accessories": ["leather belt", "slim watch", "silver cufflink", "leather cufflink"]
        }
        """
    )

    chat_preamble = [
        {
            "role": "system",
            "content": prompt_text
        },
        {
            "role": "user",
            "content": outfit_description
        }
    ]

    chat_completion = groq_client.chat.completions.create(
        messages=chat_preamble,
        model="llama3-8b-8192",
        temperature=0,
        max_tokens=512,
        top_p=1
    )

    extracted_items = chat_completion.choices[0].message.content
    return json.loads(extracted_items)

@assistant_blueprint.route('/search/<chat_id>', methods=["POST"])
def search_items(chat_id):
    try:
        chat_object_id = ObjectId(chat_id)
    except Exception:
        return jsonify({"error": "Invalid chat ID"}), 400

    db = current_app.mongo.drip
    data = request.json
    outfit_description = data.get("outfitDescription")
    chat_history = data.get("chatHistory")

    def create_filter_query(clothing_items):
        return [{
            '$match': {
                '$or': [
                    {
                        '$and': [
                            {'item_name': {'$regex': detail, '$options': 'i'}}
                            for detail in clothing_item.split(" ")
                        ]
                    }
                    for clothing_item in clothing_items
                ]
            }
        }]

    extracted_items = extract_items_from_outfit_description(outfit_description)
    pipeline = [
        {
            '$facet': {
                'tops': create_filter_query(extracted_items["tops"]),
                'bottoms': create_filter_query(extracted_items["bottoms"]),
                'shoes': create_filter_query(extracted_items["shoes"]),
                'accessories': create_filter_query(extracted_items["accessories"]),
            }
        }
    ]

    result = list(db.items.aggregate(pipeline))
    
    # Ensure result_json is a dictionary
    result_json = result[0]

    new_message = {
        "id": str(len(chat_history) + 1),
        "role": "assistant",
        "relevant_items": result_json,
        "content_type": "relevant_items"
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

    serialized_result = json.loads(json_util.dumps({"relevant_items": result_json}))

    # Ensure that jsonify is correctly used
    return serialized_result, 200
