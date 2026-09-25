from abc import ABC, abstractmethod
from typing import List, Dict, Any

class DatabaseAdapter(ABC):
    @abstractmethod
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Executes a SQL query and returns rows as dictionaries."""
        pass

    @abstractmethod
    def get_dialect_name(self) -> str:
        """Returns the SQL dialect name."""
        pass

    @abstractmethod
    def extract_table_schemas(self) -> List[Dict[str, str]]:
        """Extracts schema definitions for all user tables."""
        pass