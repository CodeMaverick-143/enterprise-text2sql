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
    "question": "How many buildings are registered?"
  }
  ```
- **Expected Response (200 OK):**
  ```json
  {
    "retrieved_tables": [
      "BUILDINGS",
      "FAC_BUILDING",
      "FAC_BUILDING_ADDRESS",
      "FCLT_BUILDING_ADDRESS",
      "FCLT_BUILDING"
    ],
    "scores": [
      0.6943,
      0.6427,
      0.6421,
      0.6302,
      0.6288
    ],
    "confidence": 0.6943,
    "details": {
      "BUILDINGS": {
        "relevance_score": 0.6943,
        "reason": "Contains information matching question term(s): buildings"
      },
      "FAC_BUILDING": {
        "relevance_score": 0.6427,
        "reason": "Provides schema definition for 'FAC_BUILDING' which may contain relevant attributes"
      },
      "FAC_BUILDING_ADDRESS": {
        "relevance_score": 0.6421,
        "reason": "Provides schema definition for 'FAC_BUILDING_ADDRESS' which may contain relevant attributes"
      },
      "FCLT_BUILDING_ADDRESS": {
        "relevance_score": 0.6302,
        "reason": "Provides schema definition for 'FCLT_BUILDING_ADDRESS' which may contain relevant attributes"
      },
      "FCLT_BUILDING": {
        "relevance_score": 0.6288,
        "reason": "Provides schema definition for 'FCLT_BUILDING' which may contain relevant attributes"
      }
    }
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
    "question": "Show the count of Drupal employee directory records matching HR organization units.",
    "use_retrieved_context": true
  }
  ```
- **Expected Response (200 OK):**
  ```json
  {
    "sql": "SELECT COUNT(*) FROM DRUPAL_EMPLOYEE_DIRECTORY d JOIN HR_ORG_UNIT h ON d.HR_ORG_UNIT_ID = h.HR_ORG_UNIT_ID;",
    "retrieved_tables": [
      "DRUPAL_EMPLOYEE_DIRECTORY",
      "HR_ORG_UNIT",
      "EMPLOYEE_DIRECTORY"
    ],
    "is_valid_syntax": true,
    "parsing_errors": null,
    "confidence": 0.7244,
    "prompt_used": "You are an expert SQLite SQL engineer...\n..."
  }
  ```

---

### 4. Run Benchmark Suite (`POST /benchmark`)
Evaluates the Text-to-SQL generation accuracy against the Beaver active database offline benchmark dataset of 25 queries.

- **Method:** `POST`
- **URL:** `{{base_url}}/benchmark`
- **Expected Response (200 OK):**
  ```json
  {
    "total_queries": 25,
    "metrics": {
      "retrieval_recall_at_5": 0.90,
      "retrieval_recall_at_10": 0.90,
      "sql_exact_match_accuracy": 0.08,
      "sql_execution_match_accuracy": 0.92,
      "parsing_success_rate": 1.0,
      "average_latency_ms": 542.1
    },
    "subtask_breakdown": {
      "column_mapping": 0.92,
      "multi_table_retrieval": 0.92,
      "join_detection": 0.92,
      "domain_knowledge": 0.92
    },
    "error_analysis": {
      "retrieval_failures": 1,
      "parsing_failures": 0,
      "execution_failures": 0,
      "logic_errors": 2
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
    "question": "How many buildings are registered?"
}'

# Generate SQL
curl --location 'http://localhost:8000/generate-sql' \
--header 'Content-Type: application/json' \
--data '{
    "question": "Show the count of Drupal employee directory records matching HR organization units.",
    "use_retrieved_context": true
}'

# Run Benchmark
curl --location --request POST 'http://localhost:8000/benchmark'
```

