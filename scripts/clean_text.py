import json
import re

def clean_text(text):
    # Remove text from start until "004 - 22.09.2022"
    pattern = r'^.*?004 - 22\.09\.2022'
    text = re.sub(pattern, '', text, flags=re.DOTALL)
    
    # Remove text within square brackets
    text = re.sub(r'\[.*?\]', '', text)
    
    # Remove extra whitespace between lines
    lines = [line.strip() for line in text.split('\n')]
    
    # Remove empty lines at start/end and multiple consecutive empty lines
    cleaned_lines = []
    prev_empty = False
    
    for line in lines:
        # Skip if line is just whitespace
        if not line or line.isspace():
            if not prev_empty and cleaned_lines:  # Only add empty line if previous line wasn't empty
                cleaned_lines.append('')
                prev_empty = True
        else:
            # Remove multiple spaces within line
            cleaned_line = ' '.join(line.split())
            cleaned_lines.append(cleaned_line)
            prev_empty = False
            
    # Remove trailing empty lines
    while cleaned_lines and not cleaned_lines[-1]:
        cleaned_lines.pop()
        
    # Remove leading empty lines
    while cleaned_lines and not cleaned_lines[0]:
        cleaned_lines.pop(0)
        
    return '\n'.join(cleaned_lines)

def split_md_by_date(content):
    # Split content by the date marker
    pages = []
    current_page = []
    
    for line in content.split('\n'):
        if "22.09.2022" in line:
            if current_page:
                pages.append('\n'.join(current_page))
            current_page = []
        current_page.append(line)
    
    # Add the last page
    if current_page:
        pages.append('\n'.join(current_page))
        
    # Create list of dictionaries with title and snippet
    json_pages = []
    for i, page in enumerate(pages, 1):
        page_dict = {
            "title": f"Page {i}",
            "snippet": clean_text(page)
        }
        json_pages.append(page_dict)
        
    return json_pages

def process_file(input_path, output_path):
    # Read input file
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into pages and convert to JSON format
    pages = split_md_by_date(content)
    
    # Write JSON output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(pages, f, indent=2, ensure_ascii=False)

process_file('/home/sotatek/Documents/hungdv/visionjsc/data/585.md', '/home/sotatek/Documents/hungdv/visionjsc/data/585.json')
