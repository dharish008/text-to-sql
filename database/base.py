from abc import ABC, abstractmethod
from typing import List, Dict, Any

class DatabaseAdapter(ABC):
    """Abstract interface that all database connectors must implement."""
    
    @abstractmethod
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Executes a SQL query and returns rows as dictionaries."""
        pass

    @abstractmethod
    def get_dialect_name(self) -> str:
        """Returns the SQL dialect name (e.g., 'PostgreSQL', 'MySQL', 'ClickHouse')."""
        pass