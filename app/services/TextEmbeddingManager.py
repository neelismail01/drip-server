from openai import OpenAI

class TextEmbeddingManager():
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def generate_text_embedding(self, text):
        response = self.client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        embedding = response.data[0].embedding
        return embedding
