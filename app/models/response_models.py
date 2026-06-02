from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RetrievalResponse(BaseModel):
    retrieved_tables: List[str] = Field(
        default_factory=list,
        description="List of table names retrieved as relevant context.",
    )
    scores: List[float] = Field(
        default_factory=list,
        description="Similarity scores for each retrieved table (higher = more relevant).",
    )
    confidence: float = Field(
        default=0.0,
        description="Aggregate confidence score for the retrieval (best similarity score).",
    )


class SQLGenerationResponse(BaseModel):
    sql: str = Field(
        default="",
        description="The generated SQL query.",
    )
    retrieved_tables: List[str] = Field(
        default_factory=list,
        description="Tables used as context for generation.",
    )
    is_valid_syntax: bool = Field(
        default=True,
        description="Whether the generated SQL passed validation.",
    )
    parsing_errors: Optional[str] = Field(
        default=None,
        description="Validation or parsing error message, if any.",
    )
    confidence: float = Field(
        default=0.0,
        description="Retrieval confidence score.",
    )
    prompt_used: str = Field(
        default="",
        description="The full prompt sent to the LLM.",
    )


class BenchmarkResponse(BaseModel):
    total_queries: int = Field(
        default=0,
        description="Number of benchmark queries evaluated.",
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Evaluation metrics including accuracy and exact match count.",
    )