import os
import psycopg2
from dotenv import load_dotenv

# LangChain imports
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

load_dotenv()

# 1. Configuration Constants
DB_PARAMS = {
    "dbname": "company_db",
    "user": "postgres",
    "password": "mysecretpassword",
    "host": "localhost",
    "port": "5432"
}

DATABASE_SCHEMA = """
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    salary INTEGER NOT NULL,
    hire_date DATE NOT NULL
);
"""

# 2. Build the AI Assembly Line
def build_sql_chain():
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert PostgreSQL developer. 
        Translate the user's natural language question into a valid SQL query.
        
        Database schema:
        {schema}
        
        RULES:
        - Return ONLY the raw SQL query.
        - Do not wrap the SQL in markdown formatting.
        - Do not include any explanations."""),
        ("human", "{question}")
    ])
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    output_parser = StrOutputParser()
    
    return prompt | llm | output_parser

# 3. The Execution Function
def ask_database(question: str, chain) -> None:
    print(f"User Question: {question}")
    
    # Step A: Let the AI generate the SQL
    print("Generating SQL...")
    generated_sql = chain.invoke({
        "schema": DATABASE_SCHEMA,
        "question": question
    })
    
    print(f"Generated Query:\n{generated_sql}\n")
    
    # Step B: Connect to the DB and execute the generated SQL
    print("Executing against PostgreSQL...")
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        # Execute the AI's query!
        cursor.execute(generated_sql)
        
        # Fetch all resulting rows
        results = cursor.fetchall()
        
        # Print the results nicely
        print("--- Database Results ---")
        if not results:
            print("No records found.")
        else:
            for row in results:
                print(row)
                
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error executing SQL: {e}")

if __name__ == "__main__":
    # Initialize the LangChain pipeline once
    sql_chain = build_sql_chain()
    
    # Test it with a real question based on our dummy data
    question1 = "Who is the highest paid employee in the Engineering department?"
    ask_database(question1, sql_chain)
    
    print("\n" + "="*40 + "\n")
    
    question2 = "How many employees were hired in 2024?"
    ask_database(question2, sql_chain)