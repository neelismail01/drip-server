import cohere

class TextEmbeddingManager():
    def __init__(self, api_key):
        self.client = cohere.Client(api_key)

    def generate_text_embedding(self, text):
        response = self.client.embed(
            texts=[text],
            model="embed-english-v3.0",
            input_type="search_document"
        )
        embedding = response.data[0].embedding
        return embedding
