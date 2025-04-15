import json

def load_documents(documents_path):
    with open(documents_path, 'r') as f:
        documents = json.load(f)
    return documents