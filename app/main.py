import logging
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
            "GET /benchmark",
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
            result = retriever.retrieve(request.question)
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


@app.get("/benchmark", response_model=BenchmarkResponse)
def run_benchmark():
    logger.info("GET /benchmark — running benchmark suite...")

    benchmark_queries = TextToSQLEvaluator.get_benchmark_queries()
    predictions: list[dict] = []

    for item in benchmark_queries:
        question = item["question"]
        ground_truth = item["ground_truth_sql"]

        try:
            result = retriever.retrieve(question)
            schema_context = "\n\n".join(result["documents"])

            prompt = PromptBuilder.build_prompt(
                question=question,
                schema_context=schema_context,
            )
            raw_response = generator.generate(prompt)
            predicted_sql = SQLGenerator.extract_sql(raw_response)
        except Exception as e:
            logger.error("Benchmark generation failed for '%s': %s", question, str(e))
            predicted_sql = ""

        predictions.append({
            "predicted_sql": predicted_sql,
            "ground_truth_sql": ground_truth,
        })

    metrics = evaluator.evaluate(predictions)

    return BenchmarkResponse(
        total_queries=metrics["total"],
        metrics=metrics,
    )