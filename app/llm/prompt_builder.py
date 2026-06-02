def build_prompt(
    question: str,
    schema_context: str
):

    return f"""
You are an expert SQLite engineer.

Database Schema:

{schema_context}

Question:

{question}

Rules:

1. Generate valid SQLite SQL.
2. Use only provided tables.
3. Return SQL only.
4. Do not explain.
"""