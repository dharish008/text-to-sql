from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # If a variable has no default value (like api_key), Pydantic will 
    # throw an error if it is missing from the .env file.
    openai_api_key: str

    # Prompt template location
    prompt_file_path: Path = Path("prompts/sql_system.txt")
    synthesis_prompt_path: Path = Path("prompts/synthesis_system.txt")
    
    # Database (with sensible defaults)
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str
    db_name: str = "company_db"
    
    # AI Config
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0
    retriever_top_k: int = 2
    agent_max_retries: int = 3
    embedding_model: str = "text-embedding-3-small"

    # Helper properties to dynamically generate connection formats
    @property
    def psycopg2_params(self) -> dict:
        return {
            "host": self.db_host,
            "port": self.db_port,
            "user": self.db_user,
            "password": self.db_password,
            "dbname": self.db_name
        }
        
    @property
    def pgvector_connection_string(self) -> str:
        return f"postgresql+psycopg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def sql_system_prompt(self) -> str:
        if not self.prompt_file_path.exists():
            raise FileNotFoundError(f"Prompt file not found at: {self.prompt_file_path}")
        return self.prompt_file_path.read_text(encoding="utf-8")

    @property
    def synthesis_system_prompt(self) -> str:
        if not self.synthesis_prompt_path.exists():
            raise FileNotFoundError(f"Missing: {self.synthesis_prompt_path}")
        return self.synthesis_prompt_path.read_text(encoding="utf-8")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

# Instantiate it once to be imported by other files
settings = Settings()