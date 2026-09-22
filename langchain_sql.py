import os
from dotenv import load_dotenv

# Import LangChain building blocks
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

load_dotenv()

# We still hardcode the schema for now (Step 2 of our master plan)
DATABASE_SCHEMA = """
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    salary INTEGER NOT NULL,
    hire_date DATE NOT NULL
);
"""

def build_sql_chain():
    # 1. The Prompt Template
    # We define placeholders using {curly_braces}
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
    
    # 2. The Model
    # temperature=0 ensures deterministic, factual output
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # 3. The Output Parser
    # This automatically extracts the string text from the LLM's response object
    output_parser = StrOutputParser()
    
    # 4. Construct the Chain using LCEL (LangChain Expression Language)
    # This pipe syntax passes data from left to right automatically
    chain = prompt | llm | output_parser
    
    return chain

if __name__ == "__main__":
    # Create the chain once
    sql_chain = build_sql_chain()
    
    user_q = "What is the average salary in the Engineering department?"
    print(f"Question: {user_q}\n")
    
    # Run the chain using the .invoke() method
    # We pass in the dictionary of variables our prompt template expects
    generated_sql = sql_chain.invoke({
        "schema": DATABASE_SCHEMA,
        "question": user_q
    })
    
    print("--- Generated SQL ---")
    print(generated_sql)