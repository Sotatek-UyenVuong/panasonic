import re
import json

def convert_text_to_json(input_file, output_file):
    # Đọc nội dung file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Tách các phần dựa trên số đầu mục (1., 2., 3., etc)
    sections = re.split(r'\n(?=\d+\. )', content)
    
    # Xử lý phần Introduction riêng nếu có
    if sections[0].startswith('Introduction'):
        intro = sections[0]
        sections = sections[1:]
        sections.insert(0, intro)

    # Tạo list để lưu các đối tượng JSON
    json_data = []

    # Xử lý từng phần
    for section in sections:
        if not section.strip():
            continue
            
        # Tìm tiêu đề
        title_match = re.match(r'^(?:\d+\. )?([^\n]+)', section.strip())
        if title_match:
            title = title_match.group(1).strip()
        else:
            title = "Untitled Section"

        # Tạo đối tượng JSON cho mỗi phần
        section_obj = {
            "title": f"Wallet Managers - {title}",
            "snippet": section.strip()
        }
        
        json_data.append(section_obj)

    # Ghi ra file JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    return json_data

# Sử dụng hàm
input_file = "raidenx_data/raidenx-docs_raidenx-on-website_wallet-managers/all_text.txt"
output_file = "raidenx_data/raidenx-docs_raidenx-on-website_wallet-managers/all_text.json"

json_data = convert_text_to_json(input_file, output_file)
print(f"Đã chuyển đổi thành công và lưu vào file {output_file}")