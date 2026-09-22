import psycopg2

# 1. Define your connection parameters
DB_PARAMS = {
    "dbname": "company_db",
    "user": "postgres",
    "password": "mysecretpassword",
    "host": "localhost",
    "port": "5432"
}

def test_connection():
    try:
        # 2. Open the pipeline
        print("Attempting to connect...")
        conn = psycopg2.connect(**DB_PARAMS)
        
        # 3. Create a cursor to execute commands
        cursor = conn.cursor()
        
        # 4. Run a basic built-in PostgreSQL command
        cursor.execute("SELECT version();")
        
        # 5. Fetch the first row of the result
        db_version = cursor.fetchone()
        print(f"\nSuccess! Connected to: {db_version[0]}")
        
        # 6. Always close the cursor and connection when done
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\nConnection failed. Error details: {e}")

if __name__ == "__main__":
    test_connection()