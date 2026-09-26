import json
import psycopg2
from psycopg2.extras import RealDictCursor

# 1. Update these variables to match your Docker container credentials
DB_CONFIG = {
    "dbname": "company_db",
    "user": "postgres",
    "password": "mysecretpassword",  # Replace with your actual password
    "host": "localhost",
    "port": "5432"
}

OUTPUT_FILE = "schema_metadata.json"

def extract_database_schema():
    query = """
    SELECT 
        table_name, 
        column_name
    FROM 
        information_schema.columns
    WHERE 
        table_schema = 'public'
        AND table_name NOT LIKE 'payment_p20%' -- Filters out monthly partitioned child tables
    ORDER BY 
        table_name, 
        ordinal_position;
    """
    
    try:
        # 2. Establish connection to the Docker PostgreSQL instance
        print(f"Connecting to database '{DB_CONFIG['dbname']}'...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 3. Execute metadata query
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # 4. Process flat rows into a grouped JSON structure: { "table": ["col1", "col2"] }
        schema_dict = {}
        for row in rows:
            table = row["table_name"]
            column = row["column_name"]
            
            if table not in schema_dict:
                schema_dict[table] = []
            
            schema_dict[table].append(column)
            
        # 5. Write the compiled dictionary out to a clean JSON file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(schema_dict, f, indent=4)
            
        print(f"🚀 Success! Schema definition saved perfectly to: {OUTPUT_FILE}")
        
    except psycopg2.OperationalError as e:
        print("\n❌ Connection Error: Could not connect to PostgreSQL.")
        print("Ensure your Docker container is running and port 5432 is mapped.")
        print(f"Details: {e}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
    finally:
        # Clean up database resources
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    extract_database_schema()
