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
      "GET /benchmark"
    ]
  }
  ```

---

### 2. Retrieve Schema Context (`POST /retrieve`)
Retrieves relevant table DDL schemas and confidence scores based on a natural language question.

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
      "employees"
    ],
    "scores": [
      0.6163,
      0.5378
    ],
    "confidence": 0.6163
  }
  ```

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

---

### 4. Run Benchmark Suite (`GET /benchmark`)
Evaluates the Text-to-SQL generation accuracy against a built-in benchmark dataset.

- **Method:** `GET`
- **URL:** `{{base_url}}/benchmark`
- **Expected Response (200 OK):**
  ```json
  {
    "total_queries": 5,
    "metrics": {
      "total": 5,
      "exact_matches": 5,
      "accuracy": 100.0
    }
  }
  ```

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
curl --location 'http://localhost:8000/benchmark'
```
