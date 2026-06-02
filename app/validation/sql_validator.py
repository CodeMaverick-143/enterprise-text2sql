import sqlparse


class SQLValidator:

    BLOCKED_KEYWORDS = [
        "DROP",
        "DELETE",
        "UPDATE",
        "ALTER",
        "TRUNCATE"
    ]

    def validate(
        self,
        sql: str
    ):

        try:

            sqlparse.parse(sql)

            upper_sql = sql.upper()

            for keyword in self.BLOCKED_KEYWORDS:

                if keyword in upper_sql:
                    return False, f"{keyword} not allowed"

            return True, None

        except Exception as e:

            return False, str(e)