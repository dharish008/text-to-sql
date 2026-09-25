from config import settings
from database.factory import get_database_adapter

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector


def sync_database_schema_to_vector_store():
    adapter = get_database_adapter(settings.database_url)
    
    print(f"Connecting to {adapter.get_dialect_name()} and extracting schemas...")
    extracted_tables = adapter.extract_table_schemas()

    if not extracted_tables:
        print("No user tables found.")
        return

    documents = []
    for item in extracted_tables:
        print(f"Extracted DDL for: {item['table_name']}")
        doc = Document(
            page_content=item["schema_text"],
            metadata={"table_name": item["table_name"], "source": "langchain_sqldatabase"}
        )
        documents.append(doc)

    print("\nIndexing into PGVector...")
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

    vector_store.add_documents(documents)
    print(f"Successfully embedded {len(documents)} table schema(s) into PGVector.")


if __name__ == "__main__":
    sync_database_schema_to_vector_store()