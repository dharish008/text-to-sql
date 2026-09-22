import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector

load_dotenv()

def test_pg_search(query: str):
    print(f"Connecting to PostgreSQL to search for: '{query}'")
    
    # 1. Initialize the embedding model (must match the model used for insertion)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # 2. Connection string for LangChain Postgres
    connection = "postgresql+psycopg://postgres:mysecretpassword@localhost:5432/company_db"
    
    # 3. Connect to the existing PGVector store
    # By using the exact same collection_name, LangChain knows to read the existing tables
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name="schema_tables",
        connection=connection,
        use_jsonb=True,
    )
    
    # 4. Create a "Retriever" that fetches the top 2 most relevant tables (k=2)
    retriever = vector_store.as_retriever(search_kwargs={"k": 2})
    
    print("-" * 40)
    
    # 5. Perform the vector similarity search
    results = retriever.invoke(query)
    
    # Print out the results
    for i, doc in enumerate(results, 1):
        print(f"\n--- Relevant Table {i} ---")
        print(doc.page_content)

if __name__ == "__main__":
    # Test 1: Should retrieve 'salaries' and 'employees'
    test_pg_search("Who gets the highest base salary and annual bonus?")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Should retrieve 'departments'
    test_pg_search("Which office location is the sales team in?")