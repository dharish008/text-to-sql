from typing import List
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from config import settings

class FewShotRetriever:
    def __init__(self, top_k: int = 2):
        self.top_k = top_k
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.openai_api_key
        )
        self.vector_store = PGVector(
            embeddings=self.embeddings,
            collection_name="fewshot_sql_examples",
            connection=settings.database_url,
            use_jsonb=True,
        )

    def get_similar_examples(self, query: str) -> str:
        """Retrieves top matching question-SQL exemplars and formats them as a prompt string."""
        docs = self.vector_store.similarity_search(query, k=self.top_k)
        if not docs:
            return ""

        formatted_blocks = []
        for idx, doc in enumerate(docs, 1):
            q = doc.metadata.get("question", doc.page_content)
            sql = doc.metadata.get("sql", "")
            formatted_blocks.append(f"-- Example {idx}:\n-- User Question: {q}\n{sql}")

        return "\n\n".join(formatted_blocks)