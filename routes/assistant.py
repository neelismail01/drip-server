from flask import (
    current_app,
    Blueprint,
    jsonify,
    request
)
import os
from groq import Groq

assistant_blueprint = Blueprint('assistant', __name__)

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

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

    chat_completion = client.chat.completions.create(
        messages=chat_preamble,
        model="llama3-8b-8192",
        temperature=0,
        max_tokens=1,
        top_p=1
    )

    response_content = chat_completion.choices[0].message.content.lower()
    misuse = True if response_content == "no" else False
    return misuse


@assistant_blueprint.route('/chat', methods=["POST"])
def chat():
    data = request.json
    chatHistory = data.get("chatHistory")
    messages = list(map(lambda item: { "role": item['role'], "content": item['content'] }, chatHistory))

    # Evaluate request for misuse (i.e. questions not related to fashion)
    most_recent_message = messages[-1]["content"]
    misuse = evaluate_chat_request_for_misuse(most_recent_message)
    if misuse:
        return "As a fashion assistant, I cannot answer this question.", 200

    chat_completion = client.chat.completions.create(
        messages=messages,
        model="llama3-8b-8192",
        temperature=1,
        max_tokens=512,
        top_p=1
    )

    return chat_completion.choices[0].message.content, 200
