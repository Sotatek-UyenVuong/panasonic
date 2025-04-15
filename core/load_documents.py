import json

def load_documents():
    with open('/Users/uyenvuong/panasonic/data/documents.json', 'r') as f:
        documents = json.load(f)
    return documents