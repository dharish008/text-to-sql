import psycopg2

DB_PARAMS = {
    "dbname": "company_db",
    "user": "postgres",
    "password": "mysecretpassword",
    "host": "localhost",
    "port": "5432"
}

try:
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    # Execute the delete command
    cursor.execute("DELETE FROM langchain_pg_embedding;")
    conn.commit() # Don't forget to commit changes!
    
    print("Successfully deleted all embeddings from pgvector.")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error clearing pgvector: {e}")
