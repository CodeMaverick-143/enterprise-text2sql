import os

from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class SQLGenerator:

    def __init__(self):

        self.client = Groq(
            api_key=os.getenv(
                "GROQ_API_KEY"
            )
        )

        self.model = os.getenv(
            "GROQ_MODEL"
        )

    def generate(
        self,
        prompt: str
    ):

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content