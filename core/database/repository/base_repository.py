import sqlite3
from typing import TypeVar, Generic, Type, List, Optional
from dataclasses import dataclass, fields
from datetime import datetime

T = TypeVar('T')

DATABASE_PATH = "database.sqlite"

class BaseRepository(Generic[T]):
    def __init__(self, model_class: Type[T]):
        self.model_class = model_class
    
    def _connect(self):
        return sqlite3.connect(DATABASE_PATH)

    def create_table(self):
        columns = ", ".join(f"{field.name} {self._get_sql_type(field.type)}" for field in fields(self.model_class))
        query = f"CREATE TABLE IF NOT EXISTS {self.model_class.__name__.lower()} ({columns})"
        
        with self._connect() as conn:
            conn.execute(query)
            conn.commit()

    def add(self, entity: T):
        column_names = ", ".join(field.name for field in fields(entity))
        placeholders = ", ".join("?" for _ in fields(entity))
        values = tuple(getattr(entity, field.name) for field in fields(entity))

        query = f"INSERT INTO {self.model_class.__name__.lower()} ({column_names}) VALUES ({placeholders})"

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            return cursor.lastrowid

    def get_by_id(self, entity_id: int) -> Optional[T]:
        query = f"SELECT * FROM {self.model_class.__name__.lower()} WHERE id = ?"
        
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (entity_id,))
            row = cursor.fetchone()
            
            if row:
                return self.model_class(*row)
            return None
    
    def get_all(self) -> List[T]:
        query = f"SELECT * FROM {self.model_class.__name__.lower()}"
        
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return [self.model_class(*row) for row in rows]

    @staticmethod
    def _get_sql_type(py_type):
        if py_type is int:
            return "INTEGER"
        elif py_type is str:
            return "TEXT"
        elif py_type is float:
            return "REAL"
        elif py_type is bool:
            return "INTEGER"
        elif py_type is datetime:
            return "TIMESTAMP"
        else:
            raise ValueError(f"Unsupported type: {py_type}")

