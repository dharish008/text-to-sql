import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Application configurations (database URLs, LLM model names, prompt texts, retry limits)
from config import settings

# Database abstraction layer to execute SQL safely via SQLAlchemy
from database.factory import get_database_adapter

# Dynamic Few-Shot exemplar retrieval service
from retrieval.fewshot_retriever import FewShotRetriever

# LangChain primitives for prompt structuring, parsing, LLM execution, and PGVector retrieval
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector


# ==============================================================================
# SECTION 1: DATABASE ADAPTER INITIALIZATION
# ==============================================================================
# Instantiates our custom SQLAlchemy database adapter.
# This object handles connection pooling, dialect inspection (e.g., PostgreSQL),
# and executing raw SQL strings returned by the LLM safely against the database engine.
db_adapter = get_database_adapter(settings.database_url)


# ==============================================================================
# SECTION 2: LANGCHAIN CHAIN & RETRIEVER BUILDERS
# ==============================================================================

def build_sql_chain():
    """
    Constructs the core Text-to-SQL generation chain.
    
    1. ChatPromptTemplate: Feeds the system prompt (containing instructions, 
       schema context, few-shot examples, and rules) plus the human request.
    2. ChatOpenAI: LLM that processes the instructions and generates SQL.
    3. StrOutputParser: Extracts and returns the plain string output from the LLM.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", settings.sql_system_prompt),
        ("human", "{question}")
    ])
    
    llm = ChatOpenAI(
        model=settings.llm_model, 
        temperature=settings.llm_temperature,
        api_key=settings.openai_api_key
    )
    
    # LangChain Expression Language (LCEL) pipeline:
    # Input Dictionary -> Formatted Messages -> LLM Output -> Clean String
    return prompt | llm | StrOutputParser()


def build_synthesis_chain():
    """
    Constructs the final summarization / answer generation chain.
    
    Takes the generated SQL query and the raw tabular JSON output from the database,
    then prompts the LLM with temperature=0.0 to synthesize a concise, factual,
    natural language response without hallucinating numbers.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", settings.synthesis_system_prompt),
        ("human", "Provide the final natural language answer.")
    ])
    
    llm = ChatOpenAI(
        model=settings.llm_model, 
        temperature=settings.llm_temperature,  # Zero temperature ensures deterministic, factual output
        api_key=settings.openai_api_key
    )
    return prompt | llm | StrOutputParser()


def get_retriever():
    """
    Initializes the schema vector store retriever connected to PGVector.
    
    Uses OpenAI's 'text-embedding-3-small' model to match the embedded 
    table schemas stored in the 'langchain_pg_embedding' table.
    
    Returns a retriever configured to fetch the top-K most semantically 
    relevant table documents for any incoming user question.
    """
    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key
    )
    
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=settings.pgvector_collection_name,
        connection=settings.database_url,
        use_jsonb=True,
    )
    
    # settings.retriever_top_k determines how many table DDL chunks get fed to the prompt
    return vector_store.as_retriever(search_kwargs={"k": settings.retriever_top_k})


# Initialize the chains and retrievers once at startup to avoid re-instantiation overhead on every request
sql_chain = build_sql_chain()
synthesis_chain = build_synthesis_chain()
schema_retriever = get_retriever()

# Initialize the dynamic Few-Shot retriever.
# top_k=2 fetches the two closest verified Question->SQL examples from our golden collection.
fewshot_retriever = FewShotRetriever(top_k=2)


# ==============================================================================
# SECTION 3: SELF-CORRECTION & EXECUTION ENGINE
# ==============================================================================

def generate_and_execute_with_retries(question: str, schema: str, fewshot_examples: str = ""):
    """
    Orchestrates SQL generation, execution, and automatic self-correction.
    
    Workflow:
    1. Sends the question, schema, and reference examples to the LLM.
    2. Attempts to execute the generated query against PostgreSQL.
    3. If PostgreSQL returns a syntax or semantic error (e.g. unknown column, 
       grouping violation, missing join), the error message is captured.
    4. On subsequent retry attempts, the error is appended to the prompt as a warning, 
       allowing the LLM to inspect its previous mistake and self-correct.
    5. If all retry attempts fail, raises an Exception containing the full error history.
    """
    error_history = ""
    dialect = db_adapter.get_dialect_name()

    for attempt in range(1, settings.agent_max_retries + 1):
        prompt_input = question
        
        # If this is a retry attempt, instruct the model explicitly on what broke previously
        if error_history:
            prompt_input += (
                f"\n\nWARNING: Previous attempts failed. "
                f"Fix the SQL according to these database errors:\n{error_history}"
            )

        # Invoke the SQL generation chain with all contextual variables
        generated_sql = sql_chain.invoke({
            "dialect": dialect,
            "schema": schema,
            "fewshot_examples": fewshot_examples,
            "question": prompt_input
        })

        # Clean any accidental markdown backticks (e.g. ```sql ... ```) if emitted by the LLM
        clean_sql = generated_sql.strip()
        if clean_sql.startswith("```sql"):
            clean_sql = clean_sql[6:]
        if clean_sql.startswith("```"):
            clean_sql = clean_sql[3:]
        if clean_sql.endswith("```"):
            clean_sql = clean_sql[:-3]
        clean_sql = clean_sql.strip()

        # Attempt query execution against the actual database
        try:
            results = db_adapter.execute_query(clean_sql)
            # Query succeeded! Return the verified query and raw data rows
            return clean_sql, results
        except Exception as e:
            # Capture both the failed query and the database driver's error trace for reflection
            error_history += f"\n- Failed SQL: {clean_sql}\n- DB Error: {str(e).strip()}\n"

    # If the loop exhausts all attempts without success, terminate with an informative error
    raise Exception(
        f"Failed to generate valid SQL after {settings.agent_max_retries} attempts. "
        f"Last errors encountered:\n{error_history}"
    )


# ==============================================================================
# SECTION 4: FASTAPI WEB SERVER & ENDPOINTS
# ==============================================================================

app = FastAPI(
    title="Text-to-SQL Agent API",
    description="Enterprise RAG-driven Text-to-SQL Agent using LangChain and PGVector"
)


class QuestionRequest(BaseModel):
    """Pydantic model defining the expected JSON request body for the /ask route."""
    question: str


@app.get("/")
def health_check():
    """Liveness probe to confirm FastAPI is running and connected to the database dialect."""
    return {
        "status": "healthy",
        "dialect": db_adapter.get_dialect_name()
    }


@app.post("/ask")
async def ask_database(payload: QuestionRequest):
    """
    Main endpoint for user interactions.
    
    Executes a three-phase pipeline:
    Phase A: Dynamic RAG (Retrieves table schemas and similar golden SQL examples).
    Phase B: Generation + Self-Correction (Generates and executes SQL with DB validation).
    Phase C: Synthesis (Transforms raw rows into natural language response).
    """

    # --------------------------------------------------------------------------
    # Phase A: Dynamic Context Retrieval (RAG)
    # --------------------------------------------------------------------------
    try:
        # 1. Retrieve the most relevant table definitions from PGVector
        relevant_docs = schema_retriever.invoke(payload.question)
        dynamic_schema = "\n\n".join([doc.page_content for doc in relevant_docs])

        # 2. Retrieve top matching verified Question->SQL pairs from the few-shot collection
        dynamic_fewshot = fewshot_retriever.get_similar_examples(payload.question)
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Context Retrieval Error: {str(e)}"
        )

    # --------------------------------------------------------------------------
    # Phase B: Generation and Execution with Self-Correction Loop
    # --------------------------------------------------------------------------
    try:
        final_sql, db_results = generate_and_execute_with_retries(
            question=payload.question, 
            schema=dynamic_schema,
            fewshot_examples=dynamic_fewshot
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Database Execution Error: {str(e)}"
        )

    # --------------------------------------------------------------------------
    # Phase C: Synthesis (Translating Results to Natural Language)
    # --------------------------------------------------------------------------
    try:
        # If the database returns 0 rows, avoid unnecessary LLM synthesis calls
        if not db_results:
            natural_language_answer = "I couldn't find any data matching your request in the database."
        else:
            # Serialize row mappings into a clean JSON string for the synthesis prompt
            results_string = json.dumps(db_results, default=str)
            natural_language_answer = synthesis_chain.invoke({
                "question": payload.question,
                "sql_query": final_sql,
                "results": results_string
            })

        # Return both the human-friendly answer and detailed technical debug objects
        return {
            "answer": natural_language_answer,
            "debug": {
                "generated_sql": final_sql,
                "raw_data": db_results
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Answer Synthesis Error: {str(e)}"
        )