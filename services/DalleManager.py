from openai import OpenAI
import os

class DalleManager:
    def __init__(self):
        self.client = OpenAI()

    def get_generated_image(self, prompt, n=1, size="1024x1024", style="vivid"):
        try:
            response = self.client.images.generate(
                prompt=prompt,
                model="dall-e-3",
                n=n,
                size=size,
                style=style
            ) 
            return response.data[0].url
        except Exception as e:
            print("Failed to generate image with Dalle.")
            return None
