import logging
from typing import Optional, Tuple

import sqlparse

logger = logging.getLogger(__name__)


class SQLValidator:
    BLOCKED_KEYWORDS = [
        "DROP",
        "DELETE",
        "UPDATE",
        "ALTER",
        "TRUNCATE",
        "INSERT",
        "CREATE",
        "REPLACE",
    ]

    def validate(self, sql: str) -> Tuple[bool, Optional[str]]:
        if not sql or not sql.strip():
            return False, "SQL query is empty."

        try:
            parsed_statements = sqlparse.parse(sql)
            if not parsed_statements:
                return False, "Failed to parse SQL: no statements found."
        except Exception as e:
            logger.error("sqlparse error: %s", str(e))
            return False, f"SQL parse error: {str(e)}"

        first_statement = parsed_statements[0]
        stmt_type = first_statement.get_type()
        if stmt_type and stmt_type.upper() != "SELECT":
            return False, f"Only SELECT queries are allowed. Got: {stmt_type}"

        upper_sql = sql.upper()
        for keyword in self.BLOCKED_KEYWORDS:
            tokens = upper_sql.split()
            if keyword in tokens:
                return False, f"Blocked operation: {keyword} is not allowed."

        if sql.count("(") != sql.count(")"):
            return False, "Mismatched parentheses in query."

        logger.info("SQL validation passed.")
        return True, None

    @staticmethod
    def format_sql(sql: str) -> str:
        return sqlparse.format(sql, reindent=True, keyword_case="upper")