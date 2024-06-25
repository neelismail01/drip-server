import cohere
from openai import OpenAI

class TextEmbeddingManager():
    def __init__(self, cohere_api_key, openai_api_key):
        self.cohere_client = cohere.Client(cohere_api_key)
        self.openai_client = OpenAI(api_key=openai_api_key)

    def get_cohere_text_embedding(self, text):
        response = self.client.embed(
            texts=[text],
            model="embed-english-v3.0",
            input_type="search_document"
        )
        return response.data[0].embedding

    def get_openai_text_embedding(self, text):
        if not text:
            return None
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
