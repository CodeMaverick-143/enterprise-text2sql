import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

BENCHMARK_QUERIES = [
    {
        "question": "How many employees are there?",
        "ground_truth_sql": "SELECT COUNT(*) FROM employees;",
    },
    {
        "question": "List all department names.",
        "ground_truth_sql": "SELECT name FROM departments;",
    },
    {
        "question": "What is the highest salary?",
        "ground_truth_sql": "SELECT MAX(salary) FROM employees;",
    },
    {
        "question": "Which employees are in the Engineering department?",
        "ground_truth_sql": "SELECT e.name FROM employees e JOIN departments d ON e.department_id = d.id WHERE d.name = 'Engineering';",
    },
    {
        "question": "What is the total budget across all departments?",
        "ground_truth_sql": "SELECT SUM(budget) FROM departments;",
    },
]


class TextToSQLEvaluator:
    @staticmethod
    def normalize_sql(sql: str) -> str:
        normalized = " ".join(sql.lower().strip().split())
        if normalized.endswith(";"):
            normalized = normalized[:-1].strip()
        return normalized

    @staticmethod
    def exact_match(predicted_sql: str, ground_truth_sql: str) -> bool:
        if not predicted_sql or not ground_truth_sql:
            return False

        p = TextToSQLEvaluator.normalize_sql(predicted_sql)
        g = TextToSQLEvaluator.normalize_sql(ground_truth_sql)
        return p == g

    def evaluate(self, predictions: List[Dict[str, str]]) -> Dict[str, Any]:
        total = len(predictions)
        if total == 0:
            return {"total": 0, "exact_matches": 0, "accuracy": 0.0}

        matches = 0
        for pred in predictions:
            predicted = pred.get("predicted_sql", "")
            ground_truth = pred.get("ground_truth_sql", "")
            if self.exact_match(predicted, ground_truth):
                matches += 1

        accuracy = round((matches / total) * 100, 2)
        logger.info(
            "Benchmark: %d/%d exact matches (%.2f%% accuracy).",
            matches,
            total,
            accuracy,
        )

        return {
            "total": total,
            "exact_matches": matches,
            "accuracy": accuracy,
        }

    @staticmethod
    def get_benchmark_queries() -> List[Dict[str, str]]:
        return BENCHMARK_QUERIES