from openai import OpenAI
from openai.embeddings_utils import get_embedding

class TextEmbeddingManager():
    def __init__(self):
        self.client = OpenAI()

    def generate_text_embedding(self, text):
        embedding = get_embedding(text, model='text-embedding-3-small')
        return embedding
