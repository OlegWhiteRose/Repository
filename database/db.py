import psycopg2
from psycopg2 import OperationalError
from contextlib import contextmanager


class Database:
    def __init__(self):
        self.conn_params = {
            "dbname": "bank",
            "user": "postgres",
            "password": "1234",
            "host": "localhost",
            "port": "5432",
        }

    def test_connection(self):
        """Проверяет соединение с базой данных"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = psycopg2.connect(**self.conn_params)
            yield conn
        except OperationalError as e:
            print(f"Connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def execute_query(
        self, query, params=None, fetch_one=False, fetch_all=False, commit=False
    ):
        """Универсальный метод для выполнения запросов"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if commit:
                    conn.commit()
                    if "RETURNING" in query.upper():
                        return cursor.fetchone()[0] if cursor.rowcount > 0 else None
                    return cursor.rowcount
                elif fetch_one:
                    return cursor.fetchone()
                elif fetch_all:
                    return cursor.fetchall()
                else:
                    return None
