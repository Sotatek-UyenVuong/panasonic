from typing import List, Optional
from datetime import datetime
import sys
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collection_db.document import DocumentModel

document_collection = DocumentModel

async def create_document(document_id: str, link_document: str, model: Optional[str] = None) -> DocumentModel:
    try:
        logger.info(f"Creating document with ID: {document_id}")
        document = DocumentModel(
            document_id=document_id,
            link_document=link_document,
            model="mistral-ocr-latest",
            documents_path=None,  # Initialize as None
            vector_path=None      # Initialize as None
        )
        created_document = await document_collection.create(document)
        if not created_document:
            logger.error(f"Failed to create document {document_id}")
            return None
        logger.info(f"Successfully created document {document_id}")
        return created_document
    except Exception as e:
        logger.error(f"Error creating document: {str(e)}", exc_info=True)
        return None

async def get_document_by_id(document_id: str) -> Optional[DocumentModel]:
    return await document_collection.find_one({"document_id": document_id})

async def get_all_documents() -> List[DocumentModel]:
    return await document_collection.find_all().to_list()

async def update_document(document_id: str, update_data: dict) -> Optional[DocumentModel]:
    """
    Update document with new data
    update_data can include: link_document, documents_path, vector_path
    """
    update_data["updated_at"] = datetime.utcnow()
    update_query = {"$set": update_data}
    
    document = await document_collection.find_one({"document_id": document_id})
    if not document:
        return None
        
    await document.update(update_query)
    return document

async def delete_document(document_id: str) -> bool:
    document = await document_collection.find_one({"document_id": document_id})
    if document:
        await document.delete()
        return True
    return False 