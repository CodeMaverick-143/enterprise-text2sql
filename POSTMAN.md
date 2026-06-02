# Postman Testing Guide

This guide details how to import, configure, and test the Enterprise Text-to-SQL microservice endpoints using **Postman**.

---

## 1. Setup & Environment

To make testing easier, define an environment in Postman with the following variable:

| Variable | Initial Value | Description |
| :--- | :--- | :--- |
| `base_url` | `http://localhost:8000` | Local URL of the running FastAPI microservice |

Make sure all requests include the header:
- `Content-Type: application/json`

---

## 2. API Endpoints

### 1. Service Health Check
Verify the service is online and lists available endpoints.

- **Method:** `GET`
- **URL:** `{{base_url}}/`
- **Expected Response (200 OK):**
  ```json
  {
    "service": "Enterprise Text-to-SQL",
    "version": "1.0.0",
    "status": "online",
    "endpoints": [
      "POST /retrieve",
      "POST /generate-sql",
      "POST /benchmark"
    ]
  }
  ```

---

### 2. Retrieve Schema Context (`POST /retrieve`)
Retrieves relevant table DDL schemas, similarity scores, aggregate confidence, and relevance explanations per table.

- **Method:** `POST`
- **URL:** `{{base_url}}/retrieve`
- **Body (raw JSON):**
  ```json
  {
    "question": "Which departments have more than 100 students?"
  }
  ```
- **Expected Response (200 OK):**
  ```json
  {
    "retrieved_tables": [
      "departments",
      "enrollments"
    ],
    "scores": [
      0.92,
      0.87
    ],
    "confidence": 0.90,
    "details": {
      "departments": {
        "relevance_score": 0.92,
        "reason": "Question asks about departments directly"
      },
      "enrollments": {
        "relevance_score": 0.87,
        "reason": "Needed to count students per department"
      }
    }
  }
  ```

![POST /retrieve Postman Screenshot](images/postman_retrieve.png)

---

### 3. Generate SQL Query (`POST /generate-sql`)
Translates a natural language question into SQLite SQL using RAG schema context retrieval.

- **Method:** `POST`
- **URL:** `{{base_url}}/generate-sql`
- **Body (raw JSON):**
  ```json
  {
    "question": "List all employees in the Engineering department.",
    "use_retrieved_context": true
  }
  ```
- **Expected Response (200 OK):**
  ```json
  {
    "sql": "SELECT e.name FROM employees e JOIN departments d ON e.department_id = d.id WHERE d.name = 'Engineering';",
    "retrieved_tables": [
      "employees",
      "departments"
    ],
    "is_valid_syntax": true,
    "parsing_errors": null,
    "confidence": 0.6421,
    "prompt_used": "..."
  }
  ```

![POST /generate-sql Postman Screenshot](images/postman_generate_sql.png)

---

### 4. Run Benchmark Suite (`POST /benchmark`)
Evaluates the Text-to-SQL generation accuracy against a built-in benchmark dataset.

- **Method:** `POST`
- **URL:** `{{base_url}}/benchmark`
- **Expected Response (200 OK):**
  ```json
  {
    "total_queries": 25,
    "metrics": {
      "retrieval_recall_at_5": 0.88,
      "retrieval_recall_at_10": 0.92,
      "sql_exact_match_accuracy": 0.52,
      "sql_execution_match_accuracy": 0.68,
      "parsing_success_rate": 0.96,
      "average_latency_ms": 850
    },
    "subtask_breakdown": {
      "multi_table_retrieval": 0.88,
      "column_mapping": 0.72,
      "join_detection": 0.65,
      "domain_knowledge": 0.58
    },
    "error_analysis": {
      "retrieval_failures": 3,
      "parsing_failures": 1,
      "execution_failures": 8,
      "logic_errors": 6
    }
  }
  ```

![GET /benchmark Postman Screenshot](images/postman_benchmark.png)

---

## 3. Importing Requests into Postman

You can copy and paste the raw JSON curl commands below directly into Postman using the **Import** button:

```bash
# Health Check
curl --location 'http://localhost:8000/'

# Retrieve Table Schemas
curl --location 'http://localhost:8000/retrieve' \
--header 'Content-Type: application/json' \
--data '{
    "question": "Which departments have more than 100 students?"
}'

# Generate SQL
curl --location 'http://localhost:8000/generate-sql' \
--header 'Content-Type: application/json' \
--data '{
    "question": "List all employees in the Engineering department.",
    "use_retrieved_context": true
}'

# Run Benchmark
curl --location --request POST 'http://localhost:8000/benchmark'
```
