import json
import cohere
import os
from dotenv import load_dotenv
import numpy as np
import pickle
import sys

load_dotenv()

API_KEY = os.getenv("COHERE_API_KEY")
co = cohere.ClientV2(api_key=API_KEY)

def load_documents(documents_path):
    with open(documents_path, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    chunks = []
    for doc in documents:
        chunk_text = f"{doc['title']} {doc['snippet']}"
        chunks.append(chunk_text)
        
    return chunks

def batch_embed(texts, batch_size=96):
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        response = co.embed(
            texts=batch,
            model="embed-multilingual-v3.0",
            input_type="search_document",
            embedding_types=['float']
        )
        all_embeddings.extend(response.embeddings.float)
    return all_embeddings

def save_vector_database(vector_database, filepath):
    """Save vector database to file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as f:
        pickle.dump(vector_database, f)
    print(f"Vector database saved to {filepath}")

def load_vector_database(filepath):
    """Load vector database from file"""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        vector_database = pickle.load(f)
    print(f"Vector database loaded from {filepath}")
    return vector_database

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python embed_chunk.py <documents_path> <vector_output_path>")
        sys.exit(1)
        
    documents_path = sys.argv[1]
    vector_output_path = sys.argv[2]
    
    chunks = load_documents(documents_path)
    print(f"Created {len(chunks)} chunks")

    # Create embeddings for chunks
    embeddings = batch_embed(chunks) 
    print(f"Calculated {len(embeddings)} embeddings")

    # Create vector database
    vector_database = {i: np.array(embedding) for i, embedding in enumerate(embeddings)}
    
    # Save vector database
    save_vector_database(vector_database, vector_output_path)

    # Test loading
    loaded_db = load_vector_database(vector_output_path)
    if loaded_db is not None:
        print(f"Vector database loaded successfully with {len(loaded_db)} vectors")


