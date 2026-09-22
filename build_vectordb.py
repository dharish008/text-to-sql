import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

# 1. Simulate a larger database schema split into individual tables
# Notice we include a description in the DDL to help the semantic search understand the table's purpose.
TABLE_SCHEMAS = [
    """
    -- Table: employees
    -- Description: Stores basic employee information and hiring dates.
    CREATE TABLE employees (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        department_id INTEGER,
        hire_date DATE NOT NULL
    );
    """,
    """
    -- Table: departments
    -- Description: Stores company departments and their locations.
    CREATE TABLE departments (
        id SERIAL PRIMARY KEY,
        department_name VARCHAR(50) NOT NULL,
        office_location VARCHAR(100) NOT NULL
    );
    """,
    """
    -- Table: salaries
    -- Description: Stores salary, bonus, and payroll information for employees.
    CREATE TABLE salaries (
        employee_id INTEGER PRIMARY KEY,
        base_salary INTEGER NOT NULL,
        annual_bonus INTEGER,
        stock_options INTEGER
    );
    """
]

def create_vector_db():
    print("Initializing embedding model...")
    # 2. We use OpenAI's embedding model to convert text into numbers (vectors)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # 3. Convert our raw strings into LangChain Document objects
    documents = []
    for schema in TABLE_SCHEMAS:
        # We can add metadata to help us identify the table later
        doc = Document(page_content=schema.strip(), metadata={"source": "schema_extraction"})
        documents.append(doc)
        
    print(f"Creating Chroma vector store with {len(documents)} tables...")
    
    # 4. Create the database and save it to a local folder named "chroma_db"
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory="./chroma_db" # This saves the database to disk
    )
    
    print("Vector database built successfully! Check the 'chroma_db' folder.")

if __name__ == "__main__":
    create_vector_db()