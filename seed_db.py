import psycopg2

# Updated connection parameters to match our Docker container
DB_PARAMS = {
    "dbname": "company_db",
    "user": "postgres",
    "password": "mysecretpassword",
    "host": "localhost",
    "port": "5432"
}

def seed_database():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        # 1. Create a table (Data Definition Language)
        print("Creating 'employees' table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                department VARCHAR(50) NOT NULL,
                salary INTEGER NOT NULL,
                hire_date DATE NOT NULL
            );
        """)
        
        # 2. Insert dummy data (Data Manipulation Language)
        # We use a TRUNCATE first just in case you run this script multiple times
        cursor.execute("TRUNCATE TABLE employees RESTART IDENTITY;")
        
        print("Inserting dummy data...")
        insert_query = """
            INSERT INTO employees (name, department, salary, hire_date)
            VALUES (%s, %s, %s, %s);
        """
        
        dummy_data = [
            ("Alice Smith", "Engineering", 120000, "2023-01-15"),
            ("Bob Jones", "Sales", 85000, "2023-03-22"),
            ("Charlie Brown", "Engineering", 110000, "2023-06-10"),
            ("Diana Prince", "HR", 95000, "2024-02-01")
        ]
        
        # executemany is a highly efficient way to insert multiple rows at once
        cursor.executemany(insert_query, dummy_data)
        
        # 3. Commit the transaction!
        conn.commit()
        print("Database seeded successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Failed to seed database: {e}")

if __name__ == "__main__":
    seed_database()