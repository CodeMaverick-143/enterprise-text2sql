import logging
import os
from typing import List

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class Embedder:
    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = (
            model_name
            or os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        )
        logger.info("Loading embedding model: %s", self.model_name)
        self.model = SentenceTransformer(self.model_name)
        logger.info("Embedding model loaded successfully.")

    def embed(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts).tolist()