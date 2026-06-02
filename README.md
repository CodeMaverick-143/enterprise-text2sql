# Enterprise Text-to-SQL

A production-grade FastAPI microservice that converts natural language questions into executable SQLite SQL using Retrieval-Augmented Generation (RAG).

---

## Tech Stack

- **API Framework:** FastAPI
- **LLM Provider:** Groq API (llama-3.3-70b-versatile)
- **Vector Store:** ChromaDB
- **Embeddings:** Sentence Transformers (BAAI/bge-small-en-v1.5)
- **Database:** SQLite
- **Validation:** sqlparse
- **Models:** Pydantic v2
- **Language:** Python 3.11+

---

## Folder Structure

```
app/
├── main.py                     # FastAPI app with endpoints and startup logic
├── retrieval/
│   ├── embedder.py             # Sentence Transformer embedding service
│   └── retriever.py            # ChromaDB semantic schema retrieval
├── llm/
│   ├── prompt_builder.py       # Structured prompt construction with few-shot examples
│   └── generator.py            # Groq API integration and SQL extraction
├── database/
│   ├── schema_loader.py        # SQLite schema introspection and DDL generation
│   └── executor.py             # Safe read-only SQL execution
├── validation/
│   └── sql_validator.py        # Syntax validation and destructive query blocking
├── benchmark/
│   └── evaluator.py            # Exact-match accuracy evaluation
└── models/
    ├── request_models.py       # Pydantic request schemas
    └── response_models.py      # Pydantic response schemas
```

---

## Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment

Create a `.env` file in the project root:

```ini
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
DATABASE_URL=sqlite:///./data/enterprise.db
CHROMA_DB_PATH=./data/chroma_db
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

### 3. Start the Server

```bash
uv run uvicorn app.main:app --reload --port 8000
```

### 4. Open API Docs

Visit [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive Swagger UI.

---

## API Endpoints

### `POST /retrieve`

Retrieve the most relevant table schemas for a natural language question.

**Request:**

```json
{
  "question": "Which departments have more than 100 students?"
}
```

**Response:**

```json
{
  "retrieved_tables": ["departments", "students"],
  "scores": [0.8542, 0.7231],
  "confidence": 0.8542
}
```

![POST /retrieve Screenshot](images/postman_retrieve.png)

---

### `POST /generate-sql`

Generate a SQL query from a natural language question using RAG context.

**Request:**

```json
{
  "question": "Which departments have more than 100 students?",
  "use_retrieved_context": true
}
```

**Response:**

```json
{
  "sql": "SELECT d.name FROM departments d JOIN students s ON d.id = s.department_id GROUP BY d.name HAVING COUNT(s.id) > 100;",
  "retrieved_tables": ["departments", "students"],
  "is_valid_syntax": true,
  "parsing_errors": null,
  "confidence": 0.8542,
  "prompt_used": "..."
}
```

![POST /generate-sql Screenshot](images/postman_generate_sql.png)

---

### `GET /benchmark`

Run the built-in benchmark suite and return accuracy metrics.

**Response:**

```json
{
  "total_queries": 5,
  "metrics": {
    "total": 5,
    "exact_matches": 3,
    "accuracy": 60.0
  }
}
```

![GET /benchmark Screenshot](images/postman_benchmark.png)

---

## Pipeline Architecture

```
User Question
     │
     ▼
┌─────────────┐     ┌──────────────┐
│  Embedder   │────▶│  ChromaDB    │
│  (BGE)      │     │  (Retriever) │
└─────────────┘     └──────┬───────┘
                           │ Top-K schemas
                           ▼
                    ┌──────────────┐
                    │ Prompt       │
                    │ Builder      │
                    └──────┬───────┘
                           │ Structured prompt
                           ▼
                    ┌──────────────┐
                    │ Groq LLM    │
                    │ (Generator)  │
                    └──────┬───────┘
                           │ Raw SQL
                           ▼
                    ┌──────────────┐
                    │ SQL          │
                    │ Validator    │
                    └──────┬───────┘
                           │ Validated SQL
                           ▼
                    ┌──────────────┐
                    │ SQL          │
                    │ Executor     │
                    └──────────────┘
```

---

## Security Guardrails

- **SELECT-only enforcement:** Only SELECT queries are permitted. The validator blocks DROP, DELETE, UPDATE, ALTER, TRUNCATE, INSERT, CREATE, and REPLACE.
- **sqlparse validation:** All generated SQL is parsed and validated before execution.
- **Read-only execution:** The SQLite executor operates in read-only mode with no write capabilities.
