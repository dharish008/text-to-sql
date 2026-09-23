import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from config import settings

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector

# --- 1. Initialize AI Components ---
def build_sql_chain():
    prompt = ChatPromptTemplate.from_messages([
        ("system", settings.sql_system_prompt),
        ("human", "{question}")
    ])
    
    llm = ChatOpenAI(
        model=settings.llm_model, 
        temperature=settings.llm_temperature,
        api_key=settings.openai_api_key
    )
    return prompt | llm | StrOutputParser()

def build_synthesis_chain():
    prompt = ChatPromptTemplate.from_messages([
        ("system", settings.synthesis_system_prompt),
        ("human", "Provide the natural language answer.")
    ])
    
    llm = ChatOpenAI(
        model=settings.llm_model, 
        temperature=0.0,  # Use 0.0 for strict factual alignment
        api_key=settings.openai_api_key
    )
    return prompt | llm | StrOutputParser()



def get_retriever():
    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key
    )
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name="schema_tables",
        connection=settings.pgvector_connection_string,
        use_jsonb=True,
    )
    return vector_store.as_retriever(search_kwargs={"k": settings.retriever_top_k})

sql_chain = build_sql_chain()
schema_retriever = get_retriever()
# Initialize it globally next to your other components
synthesis_chain = build_synthesis_chain()

# --- 2. The Agent Loop with Self-Correction ---
def generate_and_execute_with_retries(question: str, schema: str):
    error_history = ""
    
    for attempt in range(1, settings.agent_max_retries + 1):
        prompt_input = question
        if error_history:
            prompt_input += f"\n\nFix the SQL based on these errors:\n{error_history}"
            
        generated_sql = sql_chain.invoke({
            "schema": schema,
            "question": prompt_input
        })
        
        try:
            conn = psycopg2.connect(**settings.psycopg2_params)
            cursor = conn.cursor()
            cursor.execute(generated_sql)
            
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            return generated_sql, results
            
        except psycopg2.Error as e:
            error_history += f"\n- SQL: {generated_sql}\n- Error: {str(e).strip()}\n"
            
    raise Exception(f"Failed after {settings.agent_max_retries} attempts. Last error: {error_history}")

# --- 3. FastAPI Setup ---
app = FastAPI(title="Text-to-SQL Agent API")

class QuestionRequest(BaseModel):
    question: str

# --- 4. Endpoints ---
@app.get("/")
def health_check():
    return {"status": "healthy"}

@app.post("/ask")
async def ask_database(payload: QuestionRequest):
    # Step A: Retrieve Schema
    try:
        relevant_docs = schema_retriever.invoke(payload.question)
        dynamic_schema = "\n\n".join([doc.page_content for doc in relevant_docs])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval Error: {str(e)}")

    # Step B: Generate & Execute SQL
    try:
        final_sql, db_results = generate_and_execute_with_retries(
            question=payload.question, 
            schema=dynamic_schema
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    # Step C: Synthesize the final natural language response
    try:
            import json
            
            if not db_results:
                natural_language_answer = "I couldn't find any data matching your request."
            else:
                results_string = json.dumps(db_results, default=str)
                
                # Pass both the SQL and the raw results
                natural_language_answer = synthesis_chain.invoke({
                    "question": payload.question,
                    "sql_query": final_sql,
                    "results": results_string
                })
            
            return {
                "answer": natural_language_answer,
                "debug": {
                    "generated_sql": final_sql,
                    "raw_data": db_results
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synthesis Error: {str(e)}")