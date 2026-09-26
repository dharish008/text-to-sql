from typing import List, Dict, Any
from sqlalchemy import text, create_engine, inspect
from langchain_community.utilities import SQLDatabase
from database.base import DatabaseAdapter
from config import settings
from configure.semantic_metadata import SEMANTIC_CATALOG, COLUMN_ENUMS, JOIN_PATHS


class LangChainSQLDatabaseAdapter(DatabaseAdapter):
    def __init__(self, connection_url: str):
        # sample_rows_in_table_info=3 automatically includes 3 sample rows per table
        self.db = SQLDatabase.from_uri(
            connection_url,
            include_tables=getattr(settings, "target_tables", None),
            sample_rows_in_table_info=3
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
            raw_ddl_and_samples = self.db.get_table_info(table_names=[table]).strip()

            meta = SEMANTIC_CATALOG.get(table, {})
            enums = COLUMN_ENUMS.get(table, {})
            joins = JOIN_PATHS.get(table, [])

            header = []
            if meta.get("description"):
                header.append(f"-- TABLE DESCRIPTION: {meta['description']}")

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

            if enums:
                header.append("-- LOW-CARDINALITY ALLOWED VALUES (ENUMS):")
                for col, values in enums.items():
                    val_str = ", ".join(repr(v) for v in values)
                    header.append(f"--   * {col} in [{val_str}]")

            # Append explicit multi-table join routes
            if joins:
                header.append("-- CANONICAL JOIN PATHS:")
                for path in joins:
                    header.append(f"--   * {path}")

            header_text = "\n".join(header)
            combined_content = f"{header_text}\n\n{raw_ddl_and_samples}" if header_text else raw_ddl_and_samples

            table_schemas.append({
                "table_name": table,
                "schema_text": combined_content
            })

        return table_schemas