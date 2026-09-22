import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

def test_search(query: str):
    # 1. Load the existing database from disk
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    
    # 2. Create a "Retriever" that fetches the top 2 most mathematically similar results (k=2)
    retriever = vector_store.as_retriever(search_kwargs={"k": 2})
    
    print(f"\nUser Question: '{query}'")
    print("-" * 40)
    
    # 3. Perform the search
    results = retriever.invoke(query)
    
    for i, doc in enumerate(results, 1):
        print(f"\n--- Relevant Table {i} ---")
        print(doc.page_content)

if __name__ == "__main__":
    # This should retrieve the 'salaries' and 'employees' tables, but skip 'departments'
    test_search("Who gets the highest base salary and annual bonus?")
    
    # This should retrieve the 'departments' table
    test_search("Which office location is the sales team in?")