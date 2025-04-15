from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
import logging
import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.chatbot import create_chatbot, get_chatbot_by_id
from database.document import get_document_by_id
from database.page import get_pages_by_document_id

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

class CreateChatbotRequest(BaseModel):
    document_id: str

class CreateChatbotResponse(BaseModel):
    chatbot_id: str

@router.post("/create", response_model=CreateChatbotResponse)
async def create_chatbot_from_document(request: CreateChatbotRequest):
    try:
        logger.info(f"Creating chatbot for document: {request.document_id}")
        
        # Check if document exists
        document = await get_document_by_id(request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Get all pages of the document
        pages = await get_pages_by_document_id(request.document_id)
        if not pages:
            raise HTTPException(status_code=404, detail="No pages found for this document")
            
        # Generate unique chatbot ID
        chatbot_id = str(uuid.uuid4())
        
        # Create chatbot in database
        chatbot = await create_chatbot(
            chatbot_id=chatbot_id,
            document_id=request.document_id,
            history=[]
        )
        
        if not chatbot:
            raise HTTPException(status_code=500, detail="Failed to create chatbot")
            
        logger.info(f"Successfully created chatbot: {chatbot_id}")
        return CreateChatbotResponse(chatbot_id=chatbot_id)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error creating chatbot: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{chatbot_id}/document-url")
async def get_document_url(chatbot_id: str):
    # Get chatbot
    chatbot = await get_chatbot_by_id(chatbot_id)
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    # Get document
    document = await get_document_by_id(chatbot.document.id_document)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"link_document": document.link_document} 