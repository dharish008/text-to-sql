import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from config import settings
from database.factory import get_database_adapter

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector

# --- 1. Database Adapter Initialization ---
# Uses SQLAlchemy abstraction layer under the hood
db_adapter = get_database_adapter(settings.database_url)


# --- 2. Initialize AI Components ---
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
        ("human", "Provide the final natural language answer.")
    ])
    
    llm = ChatOpenAI(
        model=settings.llm_model, 
        temperature=0.0,
        api_key=settings.openai_api_key
    )
    return prompt | llm | StrOutputParser()


def get_retriever():
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=settings.openai_api_key
    )
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=settings.pgvector_collection_name,
        connection=settings.database_url,
        use_jsonb=True,
    )
    return vector_store.as_retriever(search_kwargs={"k": settings.retriever_top_k})


sql_chain = build_sql_chain()
synthesis_chain = build_synthesis_chain()
schema_retriever = get_retriever()


# --- 3. Self-Correction Loop ---
def generate_and_execute_with_retries(question: str, schema: str):
    error_history = ""
    dialect = db_adapter.get_dialect_name()

    for attempt in range(1, settings.agent_max_retries + 1):
        prompt_input = question
        if error_history:
            prompt_input += (
                f"\n\nWARNING: Previous attempts failed. "
                f"Fix the SQL according to these database errors:\n{error_history}"
            )

        generated_sql = sql_chain.invoke({
            "dialect": dialect,
            "schema": schema,
            "question": prompt_input
        })

        try:
            results = db_adapter.execute_query(generated_sql)
            return generated_sql, results
        except Exception as e:
            error_history += f"\n- SQL: {generated_sql}\n- Error: {str(e).strip()}\n"

    raise Exception(
        f"Failed to generate valid SQL after {settings.agent_max_retries} attempts. "
        f"Last errors encountered:\n{error_history}"
    )


# --- 4. FastAPI App Definition ---
app = FastAPI(title="Text-to-SQL Agent API")


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "dialect": db_adapter.get_dialect_name()
    }


@app.post("/ask")
async def ask_database(payload: QuestionRequest):
    # Step A: Dynamic Context Retrieval (RAG)
    try:
        relevant_docs = schema_retriever.invoke(payload.question)
        dynamic_schema = "\n\n".join([doc.page_content for doc in relevant_docs])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema Retrieval Error: {str(e)}")

    # Step B: Generation and Execution with Self-Correction
    try:
        final_sql, db_results = generate_and_execute_with_retries(
            question=payload.question, 
            schema=dynamic_schema
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Execution Error: {str(e)}")

    # Step C: Synthesis (Answer Formatting)
    try:
        if not db_results:
            natural_language_answer = "I couldn't find any data matching your request."
        else:
            results_string = json.dumps(db_results, default=str)
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