import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from config import settings
from configure.golden_records import GOLDEN_PAIRS

FEWSHOT_COLLECTION = "fewshot_sql_examples"

def build_fewshot_vectorstore():
    print(f"Connecting to PGVector to populate collection: '{FEWSHOT_COLLECTION}'...")
    
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=settings.openai_api_key
    )

    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=FEWSHOT_COLLECTION,
        connection=settings.database_url,
        use_jsonb=True,
    )

    # Convert golden pairs to LangChain Documents
    documents = []
    for pair in GOLDEN_PAIRS:
        # page_content contains the question so similarity search operates on user intent
        doc = Document(
            page_content=pair["question"],
            metadata={
                "question": pair["question"],
                "sql": pair["sql"]
            }
        )
        documents.append(doc)

    vector_store.add_documents(documents)
    print(f"Successfully embedded {len(documents)} golden SQL pairs into '{FEWSHOT_COLLECTION}'.")

if __name__ == "__main__":
    build_fewshot_vectorstore()