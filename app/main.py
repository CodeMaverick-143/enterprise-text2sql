import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load env configurations
load_dotenv()

from app.models.request_models import SQLGenerationRequest, SQLValidationRequest
from app.models.response_models import SQLGenerationResponse, SQLValidationResponse
from app.database.schema_loader import SchemaLoader
from app.database.executor import SQLExecutor
from app.validation.sql_validator import SQLValidator
from app.llm.prompt_builder import PromptBuilder
from app.llm.generator import LLMGenerator
from app.benchmark.evaluator import TextToSQLEvaluator

app = FastAPI(
    title="Enterprise Text-to-SQL Platform",
    description="Secure, production-grade Natural Language to SQL generation engine for relational databases.",
    version="1.0.0"
)

# Enable CORS for the dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy-loaded singletons
def get_schema_loader() -> SchemaLoader:
    return SchemaLoader()

def get_executor() -> SQLExecutor:
    return SQLExecutor()

def get_generator() -> LLMGenerator:
    return LLMGenerator()

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Enterprise Text-to-SQL Engine",
        "features": [
            "Natural Language to SQL Generation",
            "Syntactical & Safe SQL Validation",
            "Safe Read-Only SQL Execution",
            "Schema Metadata Introspection"
        ]
    }

@app.get("/api/schema")
def get_schema(loader: SchemaLoader = Depends(get_schema_loader)):
    """
    Introspect and retrieve the relational database schema structure.
    """
    try:
        schema_info = loader.get_schema_info()
        return {
            "status": "success",
            "schema": schema_info,
            "ddl_representation": loader.get_schema_prompt_representation()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load schema: {str(e)}")

@app.post("/api/validate", response_model=SQLValidationResponse)
def validate_query(request: SQLValidationRequest):
    """
    Validate syntactical validity and safety rules for a raw SQL query.
    """
    is_valid, errors = SQLValidator.validate_sql(request.sql)
    formatted = SQLValidator.format_sql(request.sql) if is_valid else None
    return SQLValidationResponse(
        is_valid=is_valid,
        sql=request.sql,
        errors=errors,
        formatted_sql=formatted
    )

@app.post("/api/generate", response_model=SQLGenerationResponse)
def generate_sql(
    request: SQLGenerationRequest,
    loader: SchemaLoader = Depends(get_schema_loader),
    generator: LLMGenerator = Depends(get_generator),
    executor: SQLExecutor = Depends(get_executor)
):
    """
    Translate user's natural language question into SQL, validate it, and optionally execute it.
    """
    # 1. Retrieve current DDL schema
    try:
        schema_ddl = loader.get_schema_prompt_representation()
    except Exception as e:
        return SQLGenerationResponse(
            question=request.question,
            generated_sql="",
            error=f"Schema loading failed: {str(e)}"
        )

    # 2. Build Prompt and Generate SQL Query via Groq
    prompt = PromptBuilder.build_text_to_sql_prompt(request.question, schema_ddl)
    system_instruction = "You are an elite SQL generation assistant. Output ONLY valid SQL queries inside a markdown block. No conversational filler."
    
    raw_response = generator.generate(prompt, system_instruction=system_instruction)
    
    # Extract SQL from markdown code block if present
    generated_sql = raw_response
    if "```sql" in raw_response:
        generated_sql = raw_response.split("```sql")[1].split("```")[0].strip()
    elif "```" in raw_response:
        generated_sql = raw_response.split("```")[1].split("```")[0].strip()
    
    generated_sql = generated_sql.strip()

    # 3. Validate generated SQL
    is_valid, validation_errors = SQLValidator.validate_sql(generated_sql)
    if not is_valid:
        return SQLGenerationResponse(
            question=request.question,
            generated_sql=generated_sql,
            error=f"SQL Validation failed: {'; '.join(validation_errors)}"
        )

    # 4. Generate user-friendly explanation of the query
    explanation_prompt = PromptBuilder.build_explanation_prompt(request.question, generated_sql, schema_ddl)
    explanation = generator.generate(
        explanation_prompt, 
        system_instruction="You are a data analyst explaining a database query to business users."
    )

    # 5. Execute query safely (SQLite/Configured DB)
    results, exec_error = executor.execute_query(generated_sql)
    
    return SQLGenerationResponse(
        question=request.question,
        generated_sql=generated_sql,
        explanation=explanation,
        execution_results=results if not exec_error else None,
        error=exec_error
    )

@app.post("/api/benchmark")
def evaluate_benchmark(predictions: list):
    """
    Compute Text-to-SQL evaluation metrics over a test set.
    """
    evaluator = TextToSQLEvaluator()
    try:
        metrics = evaluator.evaluate_dataset(predictions)
        return {"status": "success", "metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Benchmarking failed: {str(e)}")