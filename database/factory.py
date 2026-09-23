from database.base import DatabaseAdapter
from database.sqlalchemy_adapter import SQLAlchemyAdapter

def get_database_adapter(connection_url: str) -> DatabaseAdapter:
    # Future custom implementations (e.g., BigQuery native SDK) can branch here
    return SQLAlchemyAdapter(connection_url=connection_url)