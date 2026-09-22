import psycopg2
import json

DB_PARAMS = {
    "dbname": "company_db",
    "user": "postgres",
    "password": "mysecretpassword",
    "host": "localhost",
    "port": "5432"
}

def view_all_embeddings():
    query = """
        SELECT emb.id, emb.document, emb.cmetadata, emb.embedding
        FROM langchain_pg_embedding emb
        JOIN langchain_pg_collection col ON emb.collection_id = col.uuid
        WHERE col.name = 'schema_tables';
    """
    
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        
        print(f"--- Found {len(rows)} Records inside 'schema_tables' ---\n")
        
        for row in rows:
            record_id = row[0]
            document_text = row[1]
            metadata = row[2]
            
            # The vector comes back as a string format list: '[0.123, -0.456, ...]'
            # We parse or slice it so it doesn't flood your screen with 1536 float digits
            vector_str = row[3]
            vector_preview = vector_str[:60] + "..." if vector_str else "None"
            
            print(f"🆔 ID: {record_id}")
            print(f"📄 Schema Document:\n{document_text}")
            print(f"🏷️  Metadata: {json.dumps(metadata)}")
            print(f"📐 Vector Array Preview: {vector_preview}")
            print("-" * 50)
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database Query Failed: {e}")

if __name__ == "__main__":
    view_all_embeddings()
