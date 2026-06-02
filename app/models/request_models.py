from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=500
    )


class GenerateSQLRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=500
    )

    use_retrieved_context: bool = True