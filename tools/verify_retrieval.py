import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import settings
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector

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

test_queries = [
    "gross revenue earned from customers",
    "unreturned discs that are still checked out",
    "movie duration and MPAA content rating",
]

print("=" * 60)
print("PGVECTOR SEMANTIC RETRIEVAL TEST")
print("=" * 60)

for query in test_queries:
    print(f"\nUser Query: \"{query}\"")
    results = vector_store.similarity_search(query, k=2)
    for idx, doc in enumerate(results, 1):
        tbl = doc.metadata.get("table_name")
        print(f"  [{idx}] Top Match: {tbl}")