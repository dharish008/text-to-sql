from database.base import DatabaseAdapter
from database.sqlalchemy_adapter import LangChainSQLDatabaseAdapter

def get_database_adapter(connection_url: str) -> DatabaseAdapter:
    return LangChainSQLDatabaseAdapter(connection_url=connection_url)