import logging
import os
import re

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

logger = logging.getLogger(__name__)


class SQLGenerator:
    def __init__(self) -> None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            logger.warning(
                "GROQ_API_KEY is not configured. SQL generation will fail."
            )

        self.client = Groq(api_key=api_key)
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        logger.info("SQLGenerator initialized with model: %s", self.model)

    def generate(self, prompt: str) -> str:
        logger.info("Sending prompt to Groq (%d chars)...", len(prompt))

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.choices[0].message.content
        logger.info("Received response (%d chars).", len(raw))
        return raw

    @staticmethod
    def extract_sql(raw_response: str) -> str:
        text = raw_response.strip()

        match = re.search(r"```(?:sql)?\s*\n?(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        for prefix in ("SQL:", "sql:", "SQL Query:", "Here is the SQL query:"):
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                break

        return text.strip()