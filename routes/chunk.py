import json
import re
import os
import logging
from typing import List, Dict

# Configure logging
logger = logging.getLogger(__name__)

def split_markdown_content(content: str, num_parts: int = 3) -> List[str]:
    """Split markdown content while preserving image tags."""
    # Pattern to match markdown image tags
    image_pattern = r'!\[.*?\]\([^)]+\)'
    
    # Find all image tags and their positions
    image_matches = list(re.finditer(image_pattern, content))
    image_positions = [(m.start(), m.end()) for m in image_matches]
    
    if not image_positions:
        # If no images, just split content evenly
        chunk_size = len(content) // num_parts
        chunks = []
        for i in range(num_parts):
            start = i * chunk_size
            end = start + chunk_size if i < num_parts - 1 else len(content)
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
        return chunks
    
    # Calculate content segments between images
    segments = []
    last_end = 0
    
    for start, end in image_positions:
        # Add text before image
        if start > last_end:
            segments.append(('text', content[last_end:start].strip()))
        # Add image tag
        segments.append(('image', content[start:end]))
        last_end = end
    
    # Add remaining text
    if last_end < len(content):
        segments.append(('text', content[last_end:].strip()))
    
    # Calculate total text length (excluding image tags)
    total_text_length = sum(len(seg[1]) for seg in segments if seg[0] == 'text')
    chunk_text_length = total_text_length // num_parts
    
    # Distribute segments into chunks
    chunks = []
    current_chunk = []
    current_length = 0
    
    for seg_type, seg_content in segments:
        if seg_type == 'text':
            if current_length + len(seg_content) > chunk_text_length and len(chunks) < num_parts - 1:
                # Split text at space or newline
                split_point = seg_content.rfind('\n', 0, chunk_text_length - current_length)
                if split_point == -1:
                    split_point = seg_content.rfind(' ', 0, chunk_text_length - current_length)
                if split_point == -1:
                    split_point = chunk_text_length - current_length
                
                current_chunk.append(seg_content[:split_point].strip())
                chunks.append(''.join(current_chunk))
                
                current_chunk = [seg_content[split_point:].strip()]
                current_length = len(seg_content) - split_point
            else:
                current_chunk.append(seg_content)
                current_length += len(seg_content)
        else:  # image tag
            current_chunk.append(seg_content)
    
    # Add the last chunk
    if current_chunk:
        chunks.append(''.join(current_chunk))
    
    # Handle case where we have fewer chunks than requested
    while len(chunks) < num_parts:
        chunks.append("")
    
    return chunks

def process_json_file(json_file_path: str, output_path: str) -> List[Dict]:
    """Process JSON file and split content into chunks."""
    try:
        logger.info(f"Processing JSON file: {json_file_path}")
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chunks = []
        for page in data.get('pages', []):
            page_number = page.get('page_number')
            markdown_content = page.get('markdown', '')
            
            # Split markdown content into 3 parts
            content_parts = split_markdown_content(markdown_content)
            
            # Create chunks for each part
            for i, content in enumerate(content_parts, 1):
                if content.strip():  # Only add non-empty chunks
                    chunk = {
                        'title': f"Page {page_number}",
                        'snippet': content.strip()
                    }
                    chunks.append(chunk)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save chunks to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully processed and saved {len(chunks)} chunks to {output_path}")
        return chunks
        
    except Exception as e:
        logger.error(f"Error processing JSON file: {str(e)}", exc_info=True)
        raise
