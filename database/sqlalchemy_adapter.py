from sqlalchemy import create_engine, text
from typing import List, Dict, Any
from database.base import DatabaseAdapter

class SQLAlchemyAdapter(DatabaseAdapter):
    def __init__(self, connection_url: str):
        # pool_pre_ping checks connectivity before execution
        self.engine = create_engine(connection_url, pool_pre_ping=True)

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        with self.engine.connect() as connection:
            result = connection.execute(text(query))
            if result.returns_rows:
                # result.mappings() converts rows to column-value dicts automatically
                return [dict(row) for row in result.mappings()]
            return []

    def get_dialect_name(self) -> str:
        return self.engine.dialect.name