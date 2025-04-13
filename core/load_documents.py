import json

def load_documents():
    with open('/Users/uyenbaby/Downloads/panasonic_reasoning/data/documents.json', 'r') as f:
        documents = json.load(f)
    return documents