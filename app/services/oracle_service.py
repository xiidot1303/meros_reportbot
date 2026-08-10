import oracledb
from config import (
    ORACLE_HOST,
    ORACLE_PORT,
    ORACLE_SERVICE_NAME,
    ORACLE_USER,
    ORACLE_PASSWORD,
)


class OracleClient:
    """Direct access to the SmartUp Oracle database (alternative to the SmartUp API)."""

    def __init__(self):
        self.dsn = oracledb.makedsn(
            ORACLE_HOST, ORACLE_PORT, service_name=ORACLE_SERVICE_NAME
        )

    def get_connection(self):
        return oracledb.connect(
            user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=self.dsn
        )

    def execute_query(self, query, params=None):
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params or {})
                columns = [col[0].lower() for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]

    # domain-specific query methods will be added here later
