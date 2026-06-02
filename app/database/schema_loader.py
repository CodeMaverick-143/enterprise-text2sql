import sqlite3


class SchemaLoader:

    def __init__(
        self,
        db_path
    ):
        self.db_path = db_path

    def get_schema(self):

        conn = sqlite3.connect(
            self.db_path
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            """
        )

        tables = cursor.fetchall()

        schema = {}

        for table in tables:

            table_name = table[0]

            cursor.execute(
                f"PRAGMA table_info({table_name})"
            )

            columns = cursor.fetchall()

            schema[table_name] = [
                col[1]
                for col in columns
            ]

        conn.close()

        return schema