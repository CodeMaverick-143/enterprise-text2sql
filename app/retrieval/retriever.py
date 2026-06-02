import chromadb

from app.retrieval.embedder import Embedder


class SchemaRetriever:

    def __init__(self):

        self.embedder = Embedder()

        self.client = chromadb.PersistentClient(
            path="./data/chroma_db"
        )

        self.collection = self.client.get_or_create_collection(
            name="schemas"
        )

    def add_schema(
        self,
        table_name,
        schema_text
    ):

        embedding = self.embedder.embed(
            schema_text
        )

        self.collection.add(
            ids=[table_name],
            documents=[schema_text],
            embeddings=[embedding]
        )

    def retrieve(
        self,
        question,
        top_k=5
    ):

        embedding = self.embedder.embed(
            question
        )

        result = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k
        )

        return result