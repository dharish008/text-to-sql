from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Required Secrets (Must exist in .env) ---
    openai_api_key: str

    # If left empty/None, it indexes all tables. 
    # If populated, it ONLY indexes what you specify.
    target_tables: list[str] | None = None  
    # e.g., in .env: TARGET_TABLES='["film", "customer", "rental", "payment", "category"]'
    # --- Database Settings ---
    # Universal SQLAlchemy connection string:
    # PostgreSQL: postgresql+psycopg://user:password@localhost:5432/dbname
    # MySQL:      mysql+pymysql://user:password@localhost:3306/dbname
    # DuckDB:     duckdb:///local.duckdb
    database_url: str = (
        "postgresql+psycopg://postgres:mysecretpassword@localhost:5432/company_db"
    )

    # --- Vector DB Settings ---
    # Used by PGVector to store and retrieve schema embeddings
    pgvector_collection_name: str = "schema_tables"
    retriever_top_k: int = 2

    # --- LLM Settings ---
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0
    agent_max_retries: int = 3

    # --- Prompt Template Paths ---
    sql_prompt_path: Path = Path("prompts/sql_system.txt")
    synthesis_prompt_path: Path = Path("prompts/synthesis_system.txt")

    # --- Derived Properties (Prompt File Readers) ---
    @property
    def sql_system_prompt(self) -> str:
        if not self.sql_prompt_path.exists():
            raise FileNotFoundError(f"Missing prompt file: {self.sql_prompt_path}")
        return self.sql_prompt_path.read_text(encoding="utf-8")

    @property
    def synthesis_system_prompt(self) -> str:
        if not self.synthesis_prompt_path.exists():
            raise FileNotFoundError(f"Missing prompt file: {self.synthesis_prompt_path}")
        return self.synthesis_prompt_path.read_text(encoding="utf-8")

    # --- Pydantic Settings Configuration ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignores extraneous variables in .env without raising an error
    )


# Instantiate a singleton to be imported across the application
settings = Settings()