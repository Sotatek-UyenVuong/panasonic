import json
import re

def split_content_with_overlap(content, num_parts=3, overlap=10):
    # Remove empty lines and join
    content = '\n'.join([line for line in content.split('\n') if line.strip()])
    
    # Calculate length of each part
    content_length = len(content)
    part_length = content_length // num_parts
    
    parts = []
    for i in range(num_parts):
        start = max(0, i * part_length - overlap)
        end = min(content_length, (i + 1) * part_length + overlap)
        part = content[start:end].strip()
        parts.append(part)
    
    return parts

def process_markdown(file_path):
    result = []
    current_page = ""
    current_content = []
    
    # Extract base path for images
    base_path = "/home/sotatek/Documents/Uyen/panasonic/static/images"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines:
        if line.startswith('# Page'):
            # If we have content from previous page, process it
            if current_page and current_content:
                content_text = '\n'.join(current_content)
                parts = split_content_with_overlap(content_text)
                
                # Get page number from current_page
                page_num = current_page.split()[-1]  # Assumes format "Page X"
                image_path = f"{base_path}/page_{page_num}.jpg"
                
                # Create entries for each part
                for i, part in enumerate(parts):
                    result.append({
                        "title": f"{current_page} , {image_path}",
                        "snippet": part
                    })
            
            # Start new page
            current_page = line.strip('# \n')
            current_content = []
        else:
            current_content.append(line.strip())
    
    # Process the last page
    if current_page and current_content:
        content_text = '\n'.join(current_content)
        parts = split_content_with_overlap(content_text)
        
        # Get page number for last page
        page_num = current_page.split()[-1]
        image_path = f"{base_path}/page_{page_num}.jpg"
        
        for i, part in enumerate(parts):
            result.append({
                "title": f"{current_page}, {image_path}",
                "snippet": part
            })
    
    # Save to JSON file
    with open('/Users/uyenbaby/Downloads/panasonic_reasoning/data/documents.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

# Sử dụng hàm
process_markdown('/Users/uyenbaby/Downloads/panasonic_reasoning/cffv5mk2-katsuyouguide-20240126zad-ja_secured.md')