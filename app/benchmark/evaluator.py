import json
import logging
import os
import sqlite3
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# BENCHMARK_QUERIES are dynamically loaded from Hugging Face in get_benchmark_queries()



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
        fallback_queries = [
            {
                "question": "How many buildings are registered?",
                "ground_truth_sql": "SELECT COUNT(*) FROM BUILDINGS;",
                "expected_tables": ["BUILDINGS"],
                "subtasks": ["column_mapping"]
            },
            {
                "question": "List facility floors that are in buildings.",
                "ground_truth_sql": "SELECT f.FLOOR, b.BUILDING_NAME FROM FCLT_FLOOR f JOIN FCLT_BUILDING b ON f.FCLT_BUILDING_KEY = b.FCLT_BUILDING_KEY;",
                "expected_tables": ["FCLT_FLOOR", "FCLT_BUILDING"],
                "subtasks": ["multi_table_retrieval", "join_detection"]
            },
            {
                "question": "Count the number of academic terms for the academic year 2026-2027.",
                "ground_truth_sql": "SELECT COUNT(*) FROM ACADEMIC_TERMS WHERE ACADEMIC_YEAR = '2026-2027';",
                "expected_tables": ["ACADEMIC_TERMS"],
                "subtasks": ["column_mapping", "domain_knowledge"]
            },
            {
                "question": "How many rooms are listed in the facility rooms table?",
                "ground_truth_sql": "SELECT COUNT(*) FROM FAC_ROOMS;",
                "expected_tables": ["FAC_ROOMS"],
                "subtasks": ["column_mapping"]
            },
            {
                "question": "Find Moira lists and their member names.",
                "ground_truth_sql": "SELECT m.MOIRA_LIST_NAME, d.MOIRA_LIST_MEMBER FROM MOIRA_LIST m JOIN MOIRA_LIST_DETAIL d ON m.MOIRA_LIST_KEY = d.MOIRA_LIST_KEY;",
                "expected_tables": ["MOIRA_LIST", "MOIRA_LIST_DETAIL"],
                "subtasks": ["multi_table_retrieval", "join_detection"]
            },
            {
                "question": "Show the count of Drupal employee directory records matching HR organization units.",
                "ground_truth_sql": "SELECT COUNT(*) FROM DRUPAL_EMPLOYEE_DIRECTORY d JOIN HR_ORG_UNIT h ON d.HR_ORG_UNIT_ID = h.HR_ORG_UNIT_ID;",
                "expected_tables": ["DRUPAL_EMPLOYEE_DIRECTORY", "HR_ORG_UNIT"],
                "subtasks": ["multi_table_retrieval", "join_detection"]
            },
            {
                "question": "What is the total number of HR organization units at level Department?",
                "ground_truth_sql": "SELECT COUNT(*) FROM HR_ORG_UNIT WHERE HR_ORG_UNIT_LEVEL = 'Department';",
                "expected_tables": ["HR_ORG_UNIT"],
                "subtasks": ["column_mapping", "domain_knowledge"]
            },
            {
                "question": "How many subjects are offered in the term 2014FA?",
                "ground_truth_sql": "SELECT COUNT(*) FROM LIBRARY_SUBJECT_OFFERED WHERE TERM_CODE = '2014FA';",
                "expected_tables": ["LIBRARY_SUBJECT_OFFERED"],
                "subtasks": ["column_mapping", "domain_knowledge"]
            },
            {
                "question": "Count the total number of warehouse users who have the title Administrator.",
                "ground_truth_sql": "SELECT COUNT(*) FROM WAREHOUSE_USERS WHERE TITLE = 'Administrator';",
                "expected_tables": ["WAREHOUSE_USERS"],
                "subtasks": ["column_mapping", "domain_knowledge"]
            },
            {
                "question": "How many student departments match the SIS department codes?",
                "ground_truth_sql": "SELECT COUNT(*) FROM STUDENT_DEPARTMENT s JOIN SIS_DEPARTMENT d ON s.DEPARTMENT_CODE = d.DEPARTMENT_CODE;",
                "expected_tables": ["STUDENT_DEPARTMENT", "SIS_DEPARTMENT"],
                "subtasks": ["multi_table_retrieval", "join_detection"]
            },
            {
                "question": "Show the count of all buildings in the FCLT_BUILDING table.",
                "ground_truth_sql": "SELECT COUNT(*) FROM FCLT_BUILDING;",
                "expected_tables": ["FCLT_BUILDING"],
                "subtasks": ["column_mapping"]
            },
            {
                "question": "Count the number of rooms listed in the FCLT_ROOMS table.",
                "ground_truth_sql": "SELECT COUNT(*) FROM FCLT_ROOMS;",
                "expected_tables": ["FCLT_ROOMS"],
                "subtasks": ["column_mapping"]
            },
            {
                "question": "How many people are listed in the IAP subject person table?",
                "ground_truth_sql": "SELECT COUNT(*) FROM IAP_SUBJECT_PERSON;",
                "expected_tables": ["IAP_SUBJECT_PERSON"],
                "subtasks": ["column_mapping"]
            },
            {
                "question": "What is the total number of records in the HR faculty roster with Professor rank?",
                "ground_truth_sql": "SELECT COUNT(*) FROM HR_FACULTY_ROSTER WHERE JOB_TITLE = 'Professor';",
                "expected_tables": ["HR_FACULTY_ROSTER"],
                "subtasks": ["column_mapping", "domain_knowledge"]
            },
            {
                "question": "Count all offered subjects with subject enrollment number greater than 50.",
                "ground_truth_sql": "SELECT COUNT(*) FROM SUBJECT_OFFERED WHERE SUBJECT_ENROLLMENT_NUMBER > 50;",
                "expected_tables": ["SUBJECT_OFFERED"],
                "subtasks": ["column_mapping", "domain_knowledge"]
            },
            {
                "question": "How many space usage records are stored?",
                "ground_truth_sql": "SELECT COUNT(*) FROM SPACE_USAGE;",
                "expected_tables": ["SPACE_USAGE"],
                "subtasks": ["column_mapping"]
            },
            {
                "question": "Show the count of students in the MIT student directory.",
                "ground_truth_sql": "SELECT COUNT(*) FROM MIT_STUDENT_DIRECTORY;",
                "expected_tables": ["MIT_STUDENT_DIRECTORY"],
                "subtasks": ["column_mapping"]
            },
            {
                "question": "Count the number of courses listed in the CIS course catalog.",
                "ground_truth_sql": "SELECT COUNT(*) FROM CIS_COURSE_CATALOG;",
                "expected_tables": ["CIS_COURSE_CATALOG"],
                "subtasks": ["column_mapping"]
            },
            {
                "question": "How many records are in the Moira list detail table?",
                "ground_truth_sql": "SELECT COUNT(*) FROM MOIRA_LIST_DETAIL;",
                "expected_tables": ["MOIRA_LIST_DETAIL"],
                "subtasks": ["column_mapping"]
            },
            {
                "question": "What is the count of roles in the roles fin PA table?",
                "ground_truth_sql": "SELECT COUNT(*) FROM ROLES_FIN_PA;",
                "expected_tables": ["ROLES_FIN_PA"],
                "subtasks": ["column_mapping"]
            },
            {
                "question": "How many departments exist in the SIS department table?",
                "ground_truth_sql": "SELECT COUNT(*) FROM SIS_DEPARTMENT;",
                "expected_tables": ["SIS_DEPARTMENT"],
                "subtasks": ["column_mapping"]
            },
            {
                "question": "Count the total number of CIP classification records with version 2026 (using CIP_WITH_VERSION).",
                "ground_truth_sql": "SELECT COUNT(*) FROM CIP_WITH_VERSION WHERE VERSION = '2026';",
                "expected_tables": ["CIP_WITH_VERSION"],
                "subtasks": ["column_mapping", "domain_knowledge"]
            },
            {
                "question": "Show the count of Moira list detail records matching Moira list owners.",
                "ground_truth_sql": "SELECT COUNT(*) FROM MOIRA_LIST_DETAIL d JOIN MOIRA_LIST_OWNER o ON d.MOIRA_LIST_OWNER_KEY = o.MOIRA_LIST_OWNER_KEY;",
                "expected_tables": ["MOIRA_LIST_DETAIL", "MOIRA_LIST_OWNER"],
                "subtasks": ["multi_table_retrieval", "join_detection"]
            },
            {
                "question": "How many reserve library materials are listed (using the LIBRARY_RESERVE_MATRL_DETAIL table)?",
                "ground_truth_sql": "SELECT COUNT(*) FROM LIBRARY_RESERVE_MATRL_DETAIL;",
                "expected_tables": ["LIBRARY_RESERVE_MATRL_DETAIL"],
                "subtasks": ["column_mapping"]
            },
            {
                "question": "Count the number of facility organizations (using the FCLT_ORGANIZATION table).",
                "ground_truth_sql": "SELECT COUNT(*) FROM FCLT_ORGANIZATION;",
                "expected_tables": ["FCLT_ORGANIZATION"],
                "subtasks": ["column_mapping"]
            }
        ]


        metadata_path = "./data/active_db.json"
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(
                "Active database metadata not found. Please run database initialization first (initialize_db.py)."
            )

        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        db_id = metadata.get("db_id")
        split = metadata.get("split", "dw")

        hf_token = os.getenv("HF_TOKEN")
        if hf_token:
            hf_token = hf_token.strip()
        if not hf_token:
            raise ValueError("HF_TOKEN is not set in the environment or .env file.")

        token_arg = None if hf_token == "use_env" else hf_token

        # Lazy import datasets to avoid startup delay
        from datasets import load_dataset

        logger.info("Loading beaverbench/beaver-query (split=%s) from Hugging Face...", split)
        try:
            query_dataset = load_dataset("beaverbench/beaver-query", split=split, token=token_arg)
        except Exception as e:
            logger.warning(
                "Failed to load beaverbench/beaver-query from Hugging Face: %s. "
                "Falling back to local offline Beaver benchmark queries.", str(e)
            )
            return fallback_queries

        # Filter queries matching the active db
        db_queries = [row for row in query_dataset if row["db"] == db_id]

        benchmark_queries = []
        for row in db_queries:
            gold_sql = row["sql"]
            
            # expected tables is stored as a JSON string
            try:
                expected_tables = json.loads(row["tables"])
            except Exception:
                raw_tables = row.get("tables", "")
                if raw_tables:
                    expected_tables = [t.strip().strip('"\'') for t in raw_tables.strip("[]").split(",") if t.strip()]
                else:
                    expected_tables = []

            # subtasks based on category & details
            subtasks = []
            category = row.get("category")
            if category:
                subtasks.append(category)
            detailed = row.get("detailed_category")
            if detailed:
                subtasks.append(detailed)
            if row.get("contains_domain_knowledge"):
                subtasks.append("domain_knowledge")

            benchmark_queries.append({
                "question": row["question"],
                "ground_truth_sql": gold_sql,
                "expected_tables": expected_tables,
                "subtasks": subtasks
            })

        # Limit queries to run to save Groq API credits/tokens
        max_queries = int(os.getenv("MAX_BENCHMARK_QUERIES", "25"))
        if max_queries > 0:
            benchmark_queries = benchmark_queries[:max_queries]

        logger.info("Loaded %d benchmark queries for active database '%s'.", len(benchmark_queries), db_id)
        return benchmark_queries