import logging
import os
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SQLExecutor:
    def __init__(self, db_url: str | None = None) -> None:
        raw_url = db_url or os.getenv("DATABASE_URL", "sqlite:///./data/enterprise.db")
        self.db_path = raw_url.replace("sqlite:///", "")
        logger.info("SQLExecutor initialized with db_path: %s", self.db_path)

    def execute(self, sql: str) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        logger.info("Executing SQL: %s", sql[:200])
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = [dict(row) for row in cursor.fetchall()]
            conn.close()
            logger.info("Query returned %d rows.", len(rows))
            return rows, None
        except Exception as e:
            logger.error("SQL execution error: %s", str(e))
            return None, str(e)