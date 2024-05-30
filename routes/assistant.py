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

@assistant_blueprint.route('/chat', methods=["POST"])
def chat():
    data = request.json
    chatHistory = data.get("chatHistory")
    messages = list(map(lambda item: { "role": item['role'], "content": item['content'] }, chatHistory))
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="llama3-8b-8192",
        temperature=1,
        max_tokens=512,
        top_p=1
    )

    return chat_completion.choices[0].message.content, 200
