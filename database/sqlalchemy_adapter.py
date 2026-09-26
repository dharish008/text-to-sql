from typing import List, Dict, Any
from sqlalchemy import text, create_engine, inspect
from langchain_community.utilities import SQLDatabase
from database.base import DatabaseAdapter
from config import settings
from configure.semantic_metadata import SEMANTIC_CATALOG

class LangChainSQLDatabaseAdapter(DatabaseAdapter):
    def __init__(self, connection_url: str):
        # 1. Create an engine to inspect actual table names first
        engine = create_engine(connection_url)
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())

        # 2. Vector DB tables we want to exclude if they exist
        target_ignored = {"langchain_pg_embedding", "langchain_pg_collection"}
        
        # Only ignore tables that are actually in the database
        tables_to_ignore = list(target_ignored.intersection(existing_tables))

        # 3. Initialize SQLDatabase safely
        self.db = SQLDatabase.from_uri(
            connection_url,
            include_tables=settings.target_tables, # None means include all
            sample_rows_in_table_info=0
        )

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        with self.db._engine.connect() as connection:
            result = connection.execute(text(query))
            if result.returns_rows:
                return [dict(row) for row in result.mappings()]
            return []

    def get_dialect_name(self) -> str:
        return self.db.dialect

    def extract_table_schemas(self) -> List[Dict[str, str]]:
        usable_tables = self.db.get_usable_table_names()
        table_schemas = []

        for table in usable_tables:
            raw_ddl = self.db.get_table_info(table_names=[table]).strip()
            
            # Enrich DDL with semantic metadata if defined
            meta = SEMANTIC_CATALOG.get(table)
            if meta:
                header = [f"-- TABLE DESCRIPTION: {meta.get('description', '')}"]
                
                rules = meta.get("business_rules", [])
                if rules:
                    header.append("-- BUSINESS RULES & FORMULAS:")
                    for rule in rules:
                        header.append(f"--   * {rule}")

                glossary = meta.get("column_glossary", {})
                if glossary:
                    header.append("-- COLUMN GLOSSARY:")
                    for col, desc in glossary.items():
                        header.append(f"--   * {col}: {desc}")

                header_text = "\n".join(header)
                combined_content = f"{header_text}\n\n{raw_ddl}"
            else:
                combined_content = raw_ddl

            table_schemas.append({
                "table_name": table,
                "schema_text": combined_content
            })

        return table_schemas