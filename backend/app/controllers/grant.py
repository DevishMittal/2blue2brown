import os
from openai import OpenAI
from dotenv import load_dotenv
import base64

load_dotenv()

class Grant():
    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv("NEBIUS_API_URL", "https://api.studio.nebius.ai/v1/"),
            api_key=os.getenv("LLM_KEY")
        )
        self.temperature = 0.1
        
    def code_response(self, prompt):
        response = self.client.chat.completions.create(
            model="Qwen/QwQ-32B",
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}",
                }
            ],
            temperature=self.temperature,
        )
        return response.choices[0].message.content