from openai import OpenAI

class ImageVisionManager:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def get_details_from_item_image(self, base64_image):
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                """
                                Your task is to describe an image of a provided fashion item.
                                Please classify the type of fashion item and provide details
                                about the color and fabric. Additionally, mention some occasions
                                where this item could be worn. Do not suggest other fashion items 
                                that would go well with this item. Please keep your entire 
                                description under 50 words.
                                """
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": { "url": f"data:image/jpeg;base64,{base64_image}" },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )
        return response.choices[0].message.content
