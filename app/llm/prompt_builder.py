from typing import List

FEW_SHOT_EXAMPLES = [
    {
        "question": "How many employees are in each department?",
        "sql": "SELECT d.name, COUNT(e.id) AS employee_count FROM departments d LEFT JOIN employees e ON d.id = e.department_id GROUP BY d.name;",
    },
    {
        "question": "What is the average salary by department?",
        "sql": "SELECT d.name, AVG(e.salary) AS avg_salary FROM departments d JOIN employees e ON d.id = e.department_id GROUP BY d.name;",
    },
    {
        "question": "Which department has the highest budget?",
        "sql": "SELECT name, budget FROM departments ORDER BY budget DESC LIMIT 1;",
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