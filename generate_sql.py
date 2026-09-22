import os
from dotenv import load_dotenv
from openai import OpenAI

# 1. Load environment variables from the .env file
load_dotenv()

# Initialize the LLM client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 2. Hardcode the schema for now (we will automate this later)
DATABASE_SCHEMA = """
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    salary INTEGER NOT NULL,
    hire_date DATE NOT NULL
);
"""

def generate_sql(user_question: str) -> str:
    # 3. The System Prompt: Give the LLM its identity, rules, and context
    system_prompt = f"""
    You are an expert PostgreSQL developer. 
    Your job is to translate the user's natural language question into a valid SQL query.
    
    Here is the database schema you must use:
    {DATABASE_SCHEMA}
    
    RULES:
    - Return ONLY the raw SQL query.
    - Do not wrap the SQL in markdown formatting (e.g., no ```sql ... ```).
    - Do not include any explanations or conversational text.
    """

    print(f"Asking the LLM: '{user_question}'\n")
    
    # 4. Make the API call
    response = client.chat.completions.create(
        model="gpt-4o-mini", # Fast, cheap, and smart enough for SQL
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ],
        temperature=0.0 # We want deterministic, factual SQL, not creative text
    )
    
    # Extract and return the generated SQL string
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    question = "Who are the top 2 highest paid employees in the Engineering department?"
    generated_query = generate_sql(question)
    
    print("--- Generated SQL ---")
    print(generated_query)