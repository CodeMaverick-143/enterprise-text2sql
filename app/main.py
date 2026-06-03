import logging
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.benchmark.evaluator import TextToSQLEvaluator
from app.database.executor import SQLExecutor
from app.database.schema_loader import SchemaLoader
from app.llm.generator import SQLGenerator
from app.llm.prompt_builder import PromptBuilder
from app.models.request_models import GenerateSQLRequest, RetrieveRequest
from app.models.response_models import (
    BenchmarkResponse,
    RetrievalResponse,
    SQLGenerationResponse,
)
from app.retrieval.retriever import SchemaRetriever
from app.validation.sql_validator import SQLValidator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

schema_loader: SchemaLoader | None = None
retriever: SchemaRetriever | None = None
generator: SQLGenerator | None = None
executor: SQLExecutor | None = None
validator: SQLValidator | None = None
evaluator: TextToSQLEvaluator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global schema_loader, retriever, generator, executor, validator, evaluator

    logger.info("Starting up Enterprise Text-to-SQL service...")

    schema_loader = SchemaLoader()
    retriever = SchemaRetriever()
    generator = SQLGenerator()
    executor = SQLExecutor()
    validator = SQLValidator()
    evaluator = TextToSQLEvaluator()

    schemas = schema_loader.get_all_schemas_ddl()
    if schemas:
        retriever.load_schemas(schemas)
        logger.info("Loaded %d table schemas into vector store.", len(schemas))
    else:
        logger.warning("No tables found in the database. Retrieval will be empty.")

    logger.info("Startup complete. Service is ready.")
    yield
    logger.info("Shutting down Enterprise Text-to-SQL service.")


app = FastAPI(
    title="Enterprise Text-to-SQL",
    description=(
        "Production-grade FastAPI microservice that converts natural language "
        "questions into executable SQLite SQL using Retrieval-Augmented Generation."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": "Enterprise Text-to-SQL",
        "version": "1.0.0",
        "status": "online",
        "endpoints": [
            "POST /retrieve",
            "POST /generate-sql",
            "POST /benchmark",
        ],
    }


@app.post("/retrieve", response_model=RetrievalResponse)
def retrieve_schemas(request: RetrieveRequest):
    logger.info("POST /retrieve — question: %s", request.question)

    try:
        result = retriever.retrieve(request.question)

        return RetrievalResponse(
            retrieved_tables=result["tables"],
            scores=result["scores"],
            confidence=result["confidence"],
            details=result["details"],
        )
    except Exception as e:
        logger.error("Retrieval failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")


@app.post("/generate-sql", response_model=SQLGenerationResponse)
def generate_sql(request: GenerateSQLRequest):
    logger.info("POST /generate-sql — question: %s", request.question)

    retrieved_tables: list[str] = []
    schema_context = ""
    confidence = 0.0

    if request.use_retrieved_context:
        try:
            result = retriever.retrieve(request.question, top_k=3)
            retrieved_tables = result["tables"]
            schema_context = "\n\n".join(result["documents"])
            confidence = result["confidence"]
        except Exception as e:
            logger.error("Retrieval failed during generation: %s", str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Schema retrieval failed: {str(e)}",
            )
    else:
        schema_context = schema_loader.get_full_schema_text()

    prompt = PromptBuilder.build_prompt(
        question=request.question,
        schema_context=schema_context,
    )

    try:
        raw_response = generator.generate(prompt)
        sql = SQLGenerator.extract_sql(raw_response)
    except Exception as e:
        logger.error("LLM generation failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"SQL generation failed: {str(e)}",
        )

    is_valid, error = validator.validate(sql)

    return SQLGenerationResponse(
        sql=sql,
        retrieved_tables=retrieved_tables,
        is_valid_syntax=is_valid,
        parsing_errors=error,
        confidence=confidence,
        prompt_used=prompt,
    )


@app.post("/benchmark", response_model=BenchmarkResponse)
def run_benchmark():
    logger.info("POST /benchmark — running benchmark suite...")

    try:
        benchmark_queries = TextToSQLEvaluator.get_benchmark_queries()
    except Exception as e:
        logger.error("Failed to load benchmark queries: %s", str(e))
        if "gated" in str(e).lower() or "forbidden" in str(e).lower() or "403" in str(e).lower() or "access" in str(e).lower():
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Access Denied: {str(e)}. Please visit "
                    "https://huggingface.co/datasets/beaverbench/beaver-query "
                    "and accept the dataset terms using the Hugging Face account associated with your HF_TOKEN."
                )
            )
        raise HTTPException(
            status_code=400,
            detail=f"Failed to load benchmark queries: {str(e)}"
        )

    predictions: list[dict] = []

    for item in benchmark_queries:
        question = item["question"]
        ground_truth = item["ground_truth_sql"]
        expected_tables = item.get("expected_tables", [])
        subtasks = item.get("subtasks", [])

        start_time = time.time()
        retrieved_tables = []
        is_valid = False
        error = None
        predicted_sql = ""

        try:
            result = retriever.retrieve(question, top_k=3)
            retrieved_tables = result["tables"]
            schema_context = "\n\n".join(result["documents"])

            prompt = PromptBuilder.build_prompt(
                question=question,
                schema_context=schema_context,
            )
            raw_response = generator.generate(prompt)
            predicted_sql = SQLGenerator.extract_sql(raw_response)
            is_valid, error = validator.validate(predicted_sql)
        except Exception as e:
            logger.error("Benchmark generation failed for '%s': %s", question, str(e))
            error = str(e)

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000.0

        predictions.append({
            "question": question,
            "ground_truth_sql": ground_truth,
            "predicted_sql": predicted_sql,
            "expected_tables": expected_tables,
            "retrieved_tables": retrieved_tables,
            "subtasks": subtasks,
            "is_valid_syntax": is_valid,
            "parsing_errors": error,
            "latency_ms": latency_ms
        })

    result = evaluator.evaluate(predictions)

    return BenchmarkResponse(
        total_queries=result["total_queries"],
        metrics=result["metrics"],
        subtask_breakdown=result["subtask_breakdown"],
        error_analysis=result["error_analysis"],
    )