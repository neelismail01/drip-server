from groq import Groq
import os

class GroqManager:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)

    def get_chat_response(self, messages, max_tokens, temperature=0, top_p=1):
        try:
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                max_tokens=max_tokens,
                model="llama3-8b-8192",
                temperature=temperature,
                top_p=top_p
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print("Failed to perform chat completion with Groq.")
            return None
