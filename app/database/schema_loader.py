import logging
import os
import sqlite3
from typing import Dict, List

logger = logging.getLogger(__name__)


class SchemaLoader:
    def __init__(self, db_url: str | None = None) -> None:
        raw_url = db_url or os.getenv("DATABASE_URL", "sqlite:///./data/enterprise.db")
        self.db_path = raw_url.replace("sqlite:///", "")
        logger.info("SchemaLoader initialized with db_path: %s", self.db_path)

    def get_tables(self) -> List[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        logger.info("Found %d tables: %s", len(tables), tables)
        return tables

    def get_columns(self, table_name: str) -> List[Dict[str, str]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append({
                "name": row[1],
                "type": row[2] or "TEXT",
                "notnull": bool(row[3]),
                "pk": bool(row[5]),
            })
        conn.close()
        return columns

    def get_foreign_keys(self, table_name: str) -> List[Dict[str, str]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fks = []
        for row in cursor.fetchall():
            fks.append({
                "from_col": row[3],
                "to_table": row[2],
                "to_col": row[4],
            })
        conn.close()
        return fks

    def get_table_ddl(self, table_name: str) -> str:
        columns = self.get_columns(table_name)
        fks = self.get_foreign_keys(table_name)

        col_lines = []
        for col in columns:
            parts = [f"  {col['name']} {col['type']}"]
            if col["pk"]:
                parts.append("PRIMARY KEY")
            if col["notnull"]:
                parts.append("NOT NULL")
            col_lines.append(" ".join(parts))

        for fk in fks:
            col_lines.append(
                f"  FOREIGN KEY ({fk['from_col']}) REFERENCES {fk['to_table']}({fk['to_col']})"
            )

        body = ",\n".join(col_lines)
        return f"CREATE TABLE {table_name} (\n{body}\n);"

    def get_all_schemas_ddl(self) -> Dict[str, str]:
        schemas: Dict[str, str] = {}
        for table_name in self.get_tables():
            schemas[table_name] = self.get_table_ddl(table_name)
        return schemas

    def get_full_schema_text(self) -> str:
        schemas = self.get_all_schemas_ddl()
        return "\n\n".join(schemas.values())