from pydantic import BaseModel
from typing import List, Dict, Optional


class RetrievalResponse(BaseModel):
    retrieved_tables: List[str]
    scores: List[float]
    confidence: float
    details: Dict


class SQLGenerationResponse(BaseModel):
    sql: str
    retrieved_tables: List[str]
    is_valid_syntax: bool
    parsing_errors: Optional[str]
    confidence: float
    prompt_used: str