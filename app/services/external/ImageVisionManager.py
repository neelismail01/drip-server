from openai import OpenAI

class ImageVisionManager:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def get_details_from_item_image(self, image_url):
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Can you describe the fashion items in this image as concisely as possible?"
                        },
                        {
                            "type": "image_url",
                            "image_url": { "url": image_url },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )

        return response.choices[0]
