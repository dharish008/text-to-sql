import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector

load_dotenv()

# 1. Simulate our database schema
TABLE_SCHEMAS = [
    """
    -- Table: employees
    -- Description: Stores basic employee information and hiring dates.
    CREATE TABLE employees (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    department VARCHAR(50) NOT NULL,
                    salary INTEGER NOT NULL,
                    hire_date DATE NOT NULL
    );
    """
]

def create_pgvector_db():
    print("Initializing embedding model...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    documents = []
    for schema in TABLE_SCHEMAS:
        doc = Document(page_content=schema.strip(), metadata={"source": "schema_extraction"})
        documents.append(doc)
        
    print("Connecting to PostgreSQL to store vectors...")
    
    # 2. Connection string for LangChain Postgres (Notice it uses postgresql+psycopg)
    connection = "postgresql+psycopg://postgres:mysecretpassword@localhost:5432/company_db"
    
    # 3. Initialize the PGVector store
    # This automatically creates a table called 'langchain_pg_embedding' in your DB!
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name="schema_tables",
        connection=connection,
        use_jsonb=True,
    )
    
    # 4. Insert the documents into the database
    vector_store.add_documents(documents)
    print("Vector database built successfully inside PostgreSQL!")

if __name__ == "__main__":
    create_pgvector_db()