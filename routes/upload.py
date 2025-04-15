from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import sys
import subprocess
from typing import List
import shutil
from datetime import datetime
import uuid
from mistralai import Mistral
from dotenv import load_dotenv
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collection_db.page import Image
from database.page import create_page, get_page_by_id, get_all_pages, update_page, delete_page
from database.document import create_document, get_document_by_id, get_all_documents, update_document, delete_document

# Import chunk processing
from routes.chunk import process_json_file

from commons.cloudflare_upload import simple_upload_to_cloudflare

router = APIRouter()

class PDFUploadRequest(BaseModel):
    pdf_url: str

class PDFUploadResponse(BaseModel):
    document_id: str

def save_processed_response(document_id: str, pdf_url: str, pages: List[dict], timestamp: str = None):
    """Save processed response to JSON file."""
    try:
        # Create data directory if it doesn't exist
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Generate timestamp if not provided
        if not timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        # Create filenames with document_id
        json_filename = f"processed_response_{document_id}_{timestamp}.json"
        documents_filename = f"documents_{document_id}.json"
        vector_filename = f"vector_{document_id}.pkl"
        
        json_filepath = os.path.join(data_dir, json_filename)
        documents_filepath = os.path.join(data_dir, documents_filename)
        vector_filepath = os.path.join(data_dir, vector_filename)
        
        logger.info(f"Saving processed response to {json_filepath}")
        
        # Structure processed data
        processed_data = {
            "document_id": document_id,
            "pdf_url": pdf_url,
            "processed_at": timestamp,
            "pages": pages
        }
        
        # Save to JSON file with utf-8 encoding
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Successfully saved processed response to {json_filepath}")
        return json_filepath, documents_filepath, vector_filepath
        
    except Exception as e:
        logger.error(f"Error saving processed response to JSON: {str(e)}", exc_info=True)
        raise

def process_chunks_and_embeddings(json_filepath: str, documents_filepath: str, vector_filepath: str):
    """Process chunks and create embeddings after saving JSON file."""
    try:
        # Step 1: Process chunks using chunk.py
        logger.info("Processing chunks from JSON file")
        process_json_file(json_filepath, documents_filepath)
        logger.info(f"Successfully created chunks in {documents_filepath}")

        # Step 2: Create embeddings using embed_chunk.py
        logger.info("Creating embeddings from chunks")
        embed_script_path = "/Users/uyenvuong/panasonic/scripts/embed_chunk.py"
        result = subprocess.run(['python', embed_script_path, documents_filepath, vector_filepath], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Successfully created embeddings")
        else:
            logger.error(f"Error creating embeddings: {result.stderr}")
            raise Exception("Failed to create embeddings")

    except Exception as e:
        logger.error(f"Error in chunk processing and embedding: {str(e)}", exc_info=True)
        raise

@router.post("/upload", response_model=PDFUploadResponse)
async def upload_pdf(request: PDFUploadRequest):
    try:
        logger.info(f"Starting PDF upload process for URL: {request.pdf_url}")
        
        # Initialize Mistral client
        load_dotenv()
        client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
        
        # Process PDF with OCR
        logger.info("Processing PDF with Mistral OCR")
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": request.pdf_url
            },
            include_image_base64=True
        )
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        logger.info(f"Generated document ID: {document_id}")
        
        # Create document in database
        logger.info("Creating document in database")
        document = await create_document(
            document_id=document_id,
            link_document=request.pdf_url
        )
        
        if not document:
            raise HTTPException(status_code=500, detail="Failed to create document in database")
            
        # Process and save each page
        processed_pages = []
        logger.info(f"Processing {len(ocr_response.pages)} pages")
        for page in ocr_response.pages:
            # Convert OCR images to our Image model
            images = [
                Image(
                    id=img.id,
                    image_b64=img.image_base64
                )
                for img in page.images
            ]
            
            # Create page in database
            page_id = f"{document_id}_page_{page.index}"
            logger.info(f"Creating page {page_id}")
            created_page = await create_page(
                document_id=document_id,
                page_id=page_id,
                page_number=page.index + 1,
                markdown=page.markdown,
                images=images
            )
            
            if not created_page:
                logger.error(f"Failed to create page {page_id}")
                raise HTTPException(status_code=500, detail=f"Failed to create page {page_id}")
                
            # Add processed page data
            processed_pages.append({
                "page_id": page_id,
                "page_number": page.index + 1,
                "markdown": page.markdown,
                "images": [
                    {
                        "id": img.id,
                        "image_b64": img.image_b64
                    }
                    for img in images
                ]
            })
        
        # Save processed response to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            json_filepath, documents_filepath, vector_filepath = save_processed_response(
                document_id=document_id,
                pdf_url=request.pdf_url,
                pages=processed_pages,
                timestamp=timestamp
            )
            
            # Process chunks and create embeddings with unique file paths
            process_chunks_and_embeddings(json_filepath, documents_filepath, vector_filepath)
            
            # Store the file paths in the document record
            await update_document(document_id, {
                "documents_path": documents_filepath,
                "vector_path": vector_filepath
            })
            
        except Exception as e:
            logger.error(f"Failed to process chunks and embeddings: {str(e)}", exc_info=True)
            # Continue even if processing fails
        
        logger.info(f"Successfully processed PDF. Document ID: {document_id}")
        return PDFUploadResponse(document_id=document_id)
        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    try:
        logger.info(f"Starting file upload process for file: {file.filename}")
        
        # Create temp directory if it doesn't exist
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        temp_filename = f"{uuid.uuid4()}{file_extension}"
        temp_filepath = os.path.join(temp_dir, temp_filename)
        
        # Save uploaded file temporarily
        try:
            with open(temp_filepath, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        finally:
            file.file.close()
            
        # Upload to Cloudflare
        logger.info("Uploading file to Cloudflare storage")
        cloudflare_path = f"pdf/{temp_filename}"
        pdf_url = simple_upload_to_cloudflare(temp_filepath, cloudflare_path)
        
        # Clean up temp file
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
            
        if not pdf_url:
            raise HTTPException(status_code=500, detail="Failed to upload file to storage")
            
        return JSONResponse(content={"pdf_url": pdf_url})
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Lưu response vào file TXT
def save_response_to_txt(response, filename="response.txt"):
    # Tạo thư mục data nếu chưa tồn tại
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Tạo đường dẫn đầy đủ
    # Đảm bảo file có đuôi .txt
    if not filename.endswith('.txt'):
        filename += '.txt'
    
    # Tạo đường dẫn đầy đủ
    filepath = os.path.join(data_dir, filename)
    
    # Lưu nội dung markdown của các trang vào file
    with open(filepath, 'w', encoding='utf-8') as f:
        for page in response.pages:
            f.write(f"\n=== Page {page.index} ===\n\n")
            f.write(page.markdown)
            f.write("\n\n")
    
    print(f"Response đã được lưu vào file TXT: {filepath}")
    return filepath