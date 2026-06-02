# Enterprise Text-to-SQL Platform

A production-grade, secure Natural Language to SQL translation, validation, and safe query execution platform.

---

## 🏗️ Folder Structure

```txt
enterprise-text2sql/
├── app/
│   ├── main.py                     # FastAPI base router & endpoints
│   ├── retrieval/
│   │   ├── embedder.py             # Modular sentence embeddings
│   │   └── retriever.py            # ChromaDB similarity search
│   ├── llm/
│   │   ├── prompt_builder.py       # SQL & Explanation prompt generators
│   │   └── generator.py            # Groq completion orchestration
│   ├── database/
│   │   ├── schema_loader.py        # Schema introspection (SQLAlchemy)
│   │   ├── executor.py             # Secure read-only sql executors
│   │   └── initialize_db.py        # Sample db initializer and seeder
│   ├── validation/
│   │   └── sql_validator.py        # Syntactical checks & protection bounds
│   ├── benchmark/
│   │   └── evaluator.py            # Exact match metrics & score cards
│   └── models/
│       ├── request_models.py       # Pydantic schemas (Incoming payload)
│       └── response_models.py      # Pydantic schemas (Outbound results)
├── data/                           # Relational and vector storage directory
├── logs/                           # System application files directory
├── .env                            # Application environment keys
├── requirements.txt                # Pinned pip dependencies
├── pyproject.toml                  # uv dependency mapping
└── README.md                       # Comprehensive guide (This document)
```

---

## ⚡ Quick Start

### 1. Prerequisites
Ensure you have `uv` installed, which resolves package mappings:
```bash
# Sync package environments
uv sync
```

### 2. Seeding Sample SQLite Database
Seed sample tables (`departments` and `employees`) into your sqlite DB for immediate querying:
```bash
.venv/bin/python app/database/initialize_db.py
```

### 3. Setup Groq API Keys
Copy and update keys inside your `.env` configuration file:
```ini
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=mixtral-8x7b-32768
```

### 4. Running the API Server
Start the dev server:
```bash
.venv/bin/uvicorn app.main:app --reload --port 8000
```
Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser to view the interactive Swagger Documentation.

---

## 🔗 Core API Endpoints

### `POST /api/generate`
Translates user natural language into standard SQL queries, parses it for safety metrics, executes it securely, and retrieves a friendly business description.
* **Payload:**
  ```json
  {
    "question": "Show me the top 3 highest earning employees in the Engineering department"
  }
  ```

### `POST /api/validate`
Validates standard SQL formats, runs syntactical evaluations, and cleans/prettifies it.
* **Payload:**
  ```json
  {
    "sql": "select * from employees where department_id=2"
  }
  ```

### `GET /api/schema`
Retrieves live database introspection information parsed into DDL prompt structures.

---

## 🛡️ Security Guardrails
* **Read-Only Constraints:** Queries are strictly scanned for write/destructive tokens (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`). Destructive scripts are blocked dynamically before entering the parser loop.
* **Result Limits:** The database executor enforces safety row limits (`limit=100`) on execution targets.
