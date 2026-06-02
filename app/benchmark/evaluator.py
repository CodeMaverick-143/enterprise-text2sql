import logging
import os
import sqlite3
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

BENCHMARK_QUERIES = [
    {
        "question": "How many employees are there?",
        "ground_truth_sql": "SELECT COUNT(*) FROM employees;",
        "expected_tables": ["employees"],
        "subtasks": ["column_mapping"]
    },
    {
        "question": "List all department names.",
        "ground_truth_sql": "SELECT name FROM departments;",
        "expected_tables": ["departments"],
        "subtasks": ["column_mapping"]
    },
    {
        "question": "What is the highest salary?",
        "ground_truth_sql": "SELECT MAX(salary) FROM employees;",
        "expected_tables": ["employees"],
        "subtasks": ["column_mapping"]
    },
    {
        "question": "Which employees are in the Engineering department?",
        "ground_truth_sql": "SELECT e.name FROM employees e JOIN departments d ON e.department_id = d.id WHERE d.name = 'Engineering';",
        "expected_tables": ["employees", "departments"],
        "subtasks": ["multi_table_retrieval", "join_detection"]
    },
    {
        "question": "What is the total budget across all departments?",
        "ground_truth_sql": "SELECT SUM(budget) FROM departments;",
        "expected_tables": ["departments"],
        "subtasks": ["column_mapping"]
    },
    {
        "question": "How many courses are offered by the Engineering department?",
        "ground_truth_sql": "SELECT COUNT(*) FROM courses c JOIN departments d ON c.department_id = d.id WHERE d.name = 'Engineering';",
        "expected_tables": ["courses", "departments"],
        "subtasks": ["multi_table_retrieval", "join_detection"]
    },
    {
        "question": "List the names of all online courses.",
        "ground_truth_sql": "SELECT name FROM courses WHERE is_online = 1;",
        "expected_tables": ["courses"],
        "subtasks": ["domain_knowledge"]
    },
    {
        "question": "What is the total student count enrolled in all courses?",
        "ground_truth_sql": "SELECT SUM(student_count) FROM enrollments;",
        "expected_tables": ["enrollments"],
        "subtasks": ["column_mapping"]
    },
    {
        "question": "Which departments have more than 100 students?",
        "ground_truth_sql": "SELECT d.name FROM departments d JOIN courses c ON d.id = c.department_id JOIN enrollments e ON c.id = e.course_id GROUP BY d.name HAVING SUM(e.student_count) > 100;",
        "expected_tables": ["departments", "courses", "enrollments"],
        "subtasks": ["multi_table_retrieval", "join_detection"]
    },
    {
        "question": "Show me departments ranked by total enrollment, excluding online courses.",
        "ground_truth_sql": "SELECT d.name, SUM(e.student_count) AS total_enrollment FROM departments d JOIN courses c ON d.id = c.department_id JOIN enrollments e ON c.id = e.course_id WHERE c.is_online = 0 GROUP BY d.name ORDER BY total_enrollment DESC;",
        "expected_tables": ["departments", "courses", "enrollments"],
        "subtasks": ["multi_table_retrieval", "join_detection", "domain_knowledge"]
    },
    {
        "question": "How many students are majoring in each department?",
        "ground_truth_sql": "SELECT d.name, COUNT(s.id) FROM departments d LEFT JOIN students s ON d.id = s.major_dept_id GROUP BY d.name;",
        "expected_tables": ["departments", "students"],
        "subtasks": ["multi_table_retrieval", "join_detection"]
    },
    {
        "question": "List the names of students enrolled in 'Introduction to Computer Science'.",
        "ground_truth_sql": "SELECT s.name FROM students s JOIN enrollments e ON s.id = e.student_id JOIN courses c ON e.course_id = c.id WHERE c.name = 'Introduction to Computer Science';",
        "expected_tables": ["students", "enrollments", "courses"],
        "subtasks": ["multi_table_retrieval", "join_detection"]
    },
    {
        "question": "What is the average salary of employees in each department?",
        "ground_truth_sql": "SELECT d.name, AVG(e.salary) FROM departments d LEFT JOIN employees e ON d.id = e.department_id GROUP BY d.name;",
        "expected_tables": ["departments", "employees"],
        "subtasks": ["multi_table_retrieval", "join_detection"]
    },
    {
        "question": "Which course has the highest number of credits?",
        "ground_truth_sql": "SELECT name, credits FROM courses ORDER BY credits DESC LIMIT 1;",
        "expected_tables": ["courses"],
        "subtasks": ["column_mapping"]
    },
    {
        "question": "Find the names of projects in the Sales department.",
        "ground_truth_sql": "SELECT p.name FROM projects p JOIN departments d ON p.department_id = d.id WHERE d.name = 'Sales';",
        "expected_tables": ["projects", "departments"],
        "subtasks": ["multi_table_retrieval", "join_detection"]
    },
    {
        "question": "What is the total budget allocated to projects in the Engineering department?",
        "ground_truth_sql": "SELECT SUM(p.budget) FROM projects p JOIN departments d ON p.department_id = d.id WHERE d.name = 'Engineering';",
        "expected_tables": ["projects", "departments"],
        "subtasks": ["multi_table_retrieval", "join_detection"]
    },
    {
        "question": "List the names of employees earning more than 100000.",
        "ground_truth_sql": "SELECT name FROM employees WHERE salary > 100000;",
        "expected_tables": ["employees"],
        "subtasks": ["column_mapping"]
    },
    {
        "question": "How many offline courses are offered by the Engineering department?",
        "ground_truth_sql": "SELECT COUNT(*) FROM courses c JOIN departments d ON c.department_id = d.id WHERE d.name = 'Engineering' AND c.is_online = 0;",
        "expected_tables": ["courses", "departments"],
        "subtasks": ["multi_table_retrieval", "join_detection", "domain_knowledge"]
    },
    {
        "question": "Which students are enrolled in online courses?",
        "ground_truth_sql": "SELECT DISTINCT s.name FROM students s JOIN enrollments e ON s.id = e.student_id JOIN courses c ON e.course_id = c.id WHERE c.is_online = 1;",
        "expected_tables": ["students", "enrollments", "courses"],
        "subtasks": ["multi_table_retrieval", "join_detection", "domain_knowledge"]
    },
    {
        "question": "Find the total enrollment count for each course.",
        "ground_truth_sql": "SELECT c.name, SUM(e.student_count) FROM courses c LEFT JOIN enrollments e ON c.id = e.course_id GROUP BY c.name;",
        "expected_tables": ["courses", "enrollments"],
        "subtasks": ["multi_table_retrieval", "join_detection"]
    },
    {
        "question": "What is the name of the department with the lowest budget?",
        "ground_truth_sql": "SELECT name, budget FROM departments ORDER BY budget ASC LIMIT 1;",
        "expected_tables": ["departments"],
        "subtasks": ["column_mapping"]
    },
    {
        "question": "List all employees who are not assigned to any department.",
        "ground_truth_sql": "SELECT name FROM employees WHERE department_id IS NULL;",
        "expected_tables": ["employees"],
        "subtasks": ["column_mapping"]
    },
    {
        "question": "Show the names of projects with a budget greater than 50000.",
        "ground_truth_sql": "SELECT name FROM projects WHERE budget > 50000;",
        "expected_tables": ["projects"],
        "subtasks": ["column_mapping"]
    },
    {
        "question": "Find the number of enrollments for each department.",
        "ground_truth_sql": "SELECT d.name, COUNT(e.student_id) FROM departments d JOIN courses c ON d.id = c.department_id JOIN enrollments e ON c.id = e.course_id GROUP BY d.name;",
        "expected_tables": ["departments", "courses", "enrollments"],
        "subtasks": ["multi_table_retrieval", "join_detection"]
    },
    {
        "question": "List all courses with their department names.",
        "ground_truth_sql": "SELECT c.name, d.name FROM courses c JOIN departments d ON c.department_id = d.id;",
        "expected_tables": ["courses", "departments"],
        "subtasks": ["multi_table_retrieval", "join_detection"]
    }
]


class TextToSQLEvaluator:
    def __init__(self) -> None:
        db_url = os.getenv("DATABASE_URL", "sqlite:///./data/enterprise.db")
        self.db_path = db_url.replace("sqlite:///", "")

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

    def check_execution_match(self, predicted_sql: str, ground_truth_sql: str) -> bool:
        if not predicted_sql:
            return False
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(ground_truth_sql)
            g_rows = cursor.fetchall()
            
            cursor.execute(predicted_sql)
            p_rows = cursor.fetchall()
            
            conn.close()
            
            g_sorted = sorted([tuple(r) for r in g_rows])
            p_sorted = sorted([tuple(r) for r in p_rows])
            return g_sorted == p_sorted
        except Exception:
            return False

    def evaluate(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(predictions)
        if total == 0:
            return {
                "total_queries": 0,
                "metrics": {},
                "subtask_breakdown": {},
                "error_analysis": {}
            }

        recalls_5 = []
        recalls_10 = []
        exact_matches = 0
        execution_matches = 0
        valid_parses = 0
        total_latency = 0.0

        subtask_matches = {}
        subtask_totals = {}

        retret_failures = 0
        parsing_failures = 0
        execution_failures = 0
        logic_errors = 0

        for pred in predictions:
            expected = pred.get("expected_tables", [])
            retrieved = pred.get("retrieved_tables", [])
            predicted_sql = pred.get("predicted_sql", "")
            ground_truth = pred.get("ground_truth_sql", "")
            is_valid = pred.get("is_valid_syntax", True)
            parsing_err = pred.get("parsing_errors")
            subtasks = pred.get("subtasks", [])
            total_latency += pred.get("latency_ms", 0.0)

            # 1. Retrieval Recall
            if expected:
                r5 = sum(1 for t in expected if t in retrieved[:5]) / len(expected)
                r10 = sum(1 for t in expected if t in retrieved[:10]) / len(expected)
                recalls_5.append(r5)
                recalls_10.append(r10)
                if r5 == 0.0:
                    retret_failures += 1
            else:
                recalls_5.append(1.0)
                recalls_10.append(1.0)

            # 2. Syntax/Parsing
            if is_valid and not parsing_err:
                valid_parses += 1
            else:
                parsing_failures += 1

            # 3. Exact Match & Execution Match
            is_em = self.exact_match(predicted_sql, ground_truth)
            if is_em:
                exact_matches += 1

            # Test execution correctness
            is_exec_match = False
            if predicted_sql:
                try:
                    is_exec_match = self.check_execution_match(predicted_sql, ground_truth)
                    if is_exec_match:
                        execution_matches += 1
                    else:
                        if is_valid and not parsing_err:
                            logic_errors += 1
                except Exception:
                    execution_failures += 1
            else:
                if not is_valid or parsing_err:
                    pass
                else:
                    execution_failures += 1

            # Subtask breakdown
            for subtask in subtasks:
                subtask_totals[subtask] = subtask_totals.get(subtask, 0) + 1
                if is_exec_match:
                    subtask_matches[subtask] = subtask_matches.get(subtask, 0) + 1

        avg_recall_5 = round(sum(recalls_5) / total, 2)
        avg_recall_10 = round(sum(recalls_10) / total, 2)
        em_acc = round((exact_matches / total), 2)
        exec_acc = round((execution_matches / total), 2)
        parse_rate = round((valid_parses / total), 2)
        avg_lat = round(total_latency / total, 2)

        breakdown = {}
        for subtask, sub_tot in subtask_totals.items():
            sub_matches = subtask_matches.get(subtask, 0)
            breakdown[subtask] = round(sub_matches / sub_tot, 2)

        metrics = {
            "retrieval_recall_at_5": avg_recall_5,
            "retrieval_recall_at_10": avg_recall_10,
            "sql_exact_match_accuracy": em_acc,
            "sql_execution_match_accuracy": exec_acc,
            "parsing_success_rate": parse_rate,
            "average_latency_ms": avg_lat
        }

        error_analysis = {
            "retrieval_failures": retret_failures,
            "parsing_failures": parsing_failures,
            "execution_failures": execution_failures,
            "logic_errors": logic_errors
        }

        return {
            "total_queries": total,
            "metrics": metrics,
            "subtask_breakdown": breakdown,
            "error_analysis": error_analysis
        }

    @staticmethod
    def get_benchmark_queries() -> List[Dict[str, Any]]:
        return BENCHMARK_QUERIES