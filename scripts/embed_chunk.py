import json
import cohere
import os
from dotenv import load_dotenv
import numpy as np
import pickle

load_dotenv()

API_KEY = os.getenv("COHERE_API_KEY")
co = cohere.ClientV2(api_key=API_KEY)

def load_documents():
    with open('/Users/uyenvuong/panasonic/data/documents.json', 'r', encoding='utf-8') as f:
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

def save_vector_database(vector_database, filepath='/Users/uyenvuong/panasonic/data/vector.pkl'):
    """Lưu vector database vào file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as f:
        pickle.dump(vector_database, f)
    print(f"Đã lưu vector database vào {filepath}")

def load_vector_database(filepath='/Users/uyenvuong/panasonic/data/vector.pkl'):
    """Load vector database từ file"""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        vector_database = pickle.load(f)
    print(f"Đã load vector database từ {filepath}")
    return vector_database

if __name__ == "__main__":
    chunks = load_documents()
    print(f"Đã tạo {len(chunks)} chunks")

    # Tạo embeddings cho chunks
    embeddings = batch_embed(chunks) 
    print(f"Đã tính toán {len(embeddings)} embeddings")

    # Tạo vector database
    vector_database = {i: np.array(embedding) for i, embedding in enumerate(embeddings)}
    
    # Lưu vector database
    save_vector_database(vector_database)

    # Test load lại
    loaded_db = load_vector_database()
    if loaded_db is not None:
        print(f"Vector database đã load có {len(loaded_db)} vectors")


