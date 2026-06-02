import logging
import os
from typing import Any, Dict, List

import chromadb

from app.retrieval.embedder import Embedder

logger = logging.getLogger(__name__)


class SchemaRetriever:
    def __init__(self, persist_directory: str | None = None) -> None:
        self.persist_directory = (
            persist_directory
            or os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
        )
        logger.info("Initializing ChromaDB at: %s", self.persist_directory)

        self.embedder = Embedder()
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="table_schemas",
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB collection 'table_schemas' ready (%d documents).",
            self.collection.count(),
        )

    def add_schema(self, table_name: str, schema_ddl: str) -> None:
        embedding = self.embedder.embed(schema_ddl)
        self.collection.upsert(
            ids=[table_name],
            documents=[schema_ddl],
            embeddings=[embedding],
        )
        logger.info("Indexed schema for table: %s", table_name)

    def load_schemas(self, schemas: Dict[str, str]) -> None:
        if not schemas:
            logger.warning("No schemas provided to load.")
            return

        table_names = list(schemas.keys())
        ddl_texts = list(schemas.values())
        embeddings = self.embedder.embed_batch(ddl_texts)

        self.collection.upsert(
            ids=table_names,
            documents=ddl_texts,
            embeddings=embeddings,
        )
        logger.info("Bulk-loaded %d table schemas into ChromaDB.", len(schemas))

    def retrieve(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        count = self.collection.count()
        if count == 0:
            logger.warning("ChromaDB collection is empty. No schemas to retrieve.")
            return {"tables": [], "documents": [], "scores": [], "confidence": 0.0}

        effective_k = min(top_k, count)

        embedding = self.embedder.embed(question)
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=effective_k,
        )

        tables: List[str] = results["ids"][0] if results["ids"] else []
        documents: List[str] = results["documents"][0] if results["documents"] else []
        distances: List[float] = results["distances"][0] if results["distances"] else []
        scores = [round(1.0 - d, 4) for d in distances]
        confidence = max(scores) if scores else 0.0

        logger.info(
            "Retrieved %d tables for question (confidence=%.4f): %s",
            len(tables),
            confidence,
            tables,
        )

        return {
            "tables": tables,
            "documents": documents,
            "scores": scores,
            "confidence": confidence,
        }