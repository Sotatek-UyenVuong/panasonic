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
    """Load documents từ JSON file"""
    with open('/Users/uyenvuong/panasonic/data/documents.json', 'r', encoding='utf-8') as f:
        documents = json.load(f)
    chunks = []
    for doc in documents:
        chunk_text = f"{doc['title']} {doc['snippet']}"
        chunks.append(chunk_text)
    return chunks

def load_vector_database(filepath='/Users/uyenvuong/panasonic/data/vector.pkl'):
    """Load vector database từ file"""
    if not os.path.exists(filepath):
        return None, None
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    chunks = load_documents()
    embeddings = [data[i] for i in range(len(chunks))]
    print(f"Đã load vector database từ {filepath}")
    return chunks, embeddings

def embed_query(query):
    """Embed query và trả về embedding"""
    response = co.embed(
        texts=[query],
        model='embed-multilingual-v3.0',
        input_type="search_query",
        embedding_types=['float']
    )
    return np.array(response.embeddings.float[0])

def cosine_similarity(a, b):
    """Tính cosine similarity giữa 2 vector"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def retrieve_and_rerank(query, chunks, embeddings, k=5, rerank_k=5):
    """Retrieve top k chunks tương tự nhất với query"""
    # Tính embedding cho query
    query_embedding = embed_query(query)
    
    # Tính similarity giữa query và tất cả chunks
    similarities = [cosine_similarity(query_embedding, chunk_embedding) 
                   for chunk_embedding in embeddings]
    
    # Lấy top k indices có similarity cao nhất
    top_indices = np.argsort(similarities)[::-1][:k]
    
    # Lấy chunks và scores tương ứng
    results = [(chunks[i], similarities[i]) for i in top_indices]
    
    return results
