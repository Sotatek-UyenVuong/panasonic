import json
import re

def extract_page_number(title):
    # Tìm số trang từ pattern "Page X" trong title
    match = re.search(r'Page (\d+)', title)
    if match:
        return int(match.group(1))
    return None

def process_documents():
    # Đọc file JSON
    with open('/home/sotatek/Documents/Uyen/panasonic/data/documents.json', 'r', encoding='utf-8') as file:
        documents = json.load(file)

    # Thêm trường page cho mỗi document
    for doc in documents:
        doc['page'] = extract_page_number(doc['title'])

    # Ghi lại vào file JSON với định dạng đẹp
    with open('/home/sotatek/Documents/Uyen/panasonic/data/documents.json', 'w', encoding='utf-8') as file:
        json.dump(documents, file, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    process_documents()