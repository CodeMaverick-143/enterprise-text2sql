import sqlite3


class SQLExecutor:

    def __init__(
        self,
        db_path
    ):
        self.db_path = db_path

    def execute(
        self,
        sql
    ):

        conn = sqlite3.connect(
            self.db_path
        )

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute(sql)

        rows = cursor.fetchall()

        conn.close()

        return [
            dict(row)
            for row in rows
        ]