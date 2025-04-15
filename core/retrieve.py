import json
import cohere
import os
from dotenv import load_dotenv
import numpy as np
import pickle

load_dotenv()

API_KEY = os.getenv("COHERE_API_KEY")
co = cohere.ClientV2(api_key=API_KEY)

def load_documents(documents_path):
    """Load documents from JSON file"""
    with open(documents_path, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    chunks = []
    for doc in documents:
        chunk_text = f"{doc['title']} {doc['snippet']}"
        chunks.append(chunk_text)
    return chunks

def load_vector_database(vector_path):
    """Load vector database from file"""
    if not os.path.exists(vector_path):
        return None, None
    with open(vector_path, 'rb') as f:
        data = pickle.load(f)
    chunks = load_documents(os.path.join(os.path.dirname(vector_path), 'documents.json'))
    embeddings = [data[i] for i in range(len(chunks))]
    print(f"Vector database loaded from {vector_path}")
    return chunks, embeddings

def embed_query(query):
    """Embed query and return embedding"""
    response = co.embed(
        texts=[query],
        model='embed-multilingual-v3.0',
        input_type="search_query",
        embedding_types=['float']
    )
    return np.array(response.embeddings.float[0])

def cosine_similarity(a, b):
    """Calculate cosine similarity between 2 vectors"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def retrieve_and_rerank(query, documents_path, vector_path, k=10, rerank_k=10):
    """Retrieve top k chunks most similar to query"""
    # Load documents and vectors
    chunks = load_documents(documents_path)
    with open(vector_path, 'rb') as f:
        vector_data = pickle.load(f)
    embeddings = [vector_data[i] for i in range(len(chunks))]
    
    # Calculate embedding for query
    query_embedding = embed_query(query)
    
    # Calculate similarity between query and all chunks
    similarities = [cosine_similarity(query_embedding, chunk_embedding) 
                   for chunk_embedding in embeddings]
    
    # Get top k indices with highest similarity
    top_indices = np.argsort(similarities)[::-1][:k]
    
    # Get corresponding chunks and scores
    results = [(chunks[i], similarities[i]) for i in top_indices]
    
    return results
