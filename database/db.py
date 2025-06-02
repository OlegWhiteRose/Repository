import psycopg2
from psycopg2 import OperationalError
from contextlib import contextmanager


class Database:
    def __init__(self):
        self.conn_params = {
            "dbname": "stocks_labs",
            "user": "postgres",
            "password": "0520",
            "host": "localhost",
            "port": "5432",
        }

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
        """Универсальный метод для выполнения запросов (упрощенный)"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if commit:
                    conn.commit()
                    # Если есть RETURNING, получаем значение
                    if "RETURNING" in query.upper():
                        return cursor.fetchone()[0] if cursor.rowcount > 0 else None
                    return (
                        cursor.rowcount
                    )  # Возвращаем кол-во измененных строк для INSERT/UPDATE/DELETE
                elif fetch_one:
                    return cursor.fetchone()
                elif fetch_all:
                    return cursor.fetchall()
                else:
                    # Для SELECT без fetch_one/fetch_all, возвращаем курсор (редко нужно)
                    # Или возвращаем None по умолчанию
                    return None
