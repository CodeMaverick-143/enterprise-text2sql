from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Natural language question to retrieve relevant table schemas for.",
    )


class GenerateSQLRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Natural language question to translate into SQL.",
    )
    use_retrieved_context: bool = Field(
        default=True,
        description="If True, use RAG to retrieve relevant schemas before generating SQL.",
    )