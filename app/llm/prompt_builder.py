from typing import List

FEW_SHOT_EXAMPLES = [
    {
        "question": "How many buildings are registered?",
        "sql": "SELECT COUNT(*) FROM BUILDINGS;",
    },
    {
        "question": "List the names of all buildings.",
        "sql": "SELECT BUILDING_NAME FROM BUILDINGS;",
    },
]


class PromptBuilder:
    @staticmethod
    def build_prompt(
        question: str,
        schema_context: str,
        few_shots: List[dict] | None = None,
    ) -> str:
        examples = few_shots if few_shots is not None else FEW_SHOT_EXAMPLES

        few_shot_block = ""
        if examples:
            few_shot_block = "\n### Examples:\n"
            for ex in examples:
                few_shot_block += f"\nQuestion: {ex['question']}\nSQL: {ex['sql']}\n"

        return f"""You are an expert SQLite SQL engineer.

### Database Schema:

{schema_context}
{few_shot_block}
### Rules:

1. Generate ONLY valid SQLite SQL.
2. Use ONLY tables and columns from the schema above.
3. Return ONLY the raw SQL query, nothing else.
4. Do NOT include explanations, markdown formatting, or code fences.
5. Use SELECT statements only. Never use INSERT, UPDATE, DELETE, DROP, ALTER, or TRUNCATE.
6. End the query with a semicolon.

### Question:

{question}

### SQL:
"""