from typing import List, Optional
from datetime import datetime
import sys
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collection_db.chatbot import Chatbot, HistoryItem, DocumentRef

chatbot_collection = Chatbot

async def create_chatbot(
    chatbot_id: str,
    document_id: str,
    history: List[HistoryItem] = None
) -> Chatbot:
    try:
        logger.info(f"Creating chatbot with ID: {chatbot_id}")
        chatbot = Chatbot(
            chatbot_id=chatbot_id,
            document=DocumentRef(id_document=document_id),
            history=history or []
        )
        created_chatbot = await chatbot_collection.create(chatbot)
        if not created_chatbot:
            logger.error(f"Failed to create chatbot {chatbot_id}")
            return None
        logger.info(f"Successfully created chatbot {chatbot_id}")
        return created_chatbot
    except Exception as e:
        logger.error(f"Error creating chatbot: {str(e)}", exc_info=True)
        return None

async def get_chatbot_by_id(chatbot_id: str) -> Optional[Chatbot]:
    return await chatbot_collection.find_one({"chatbot_id": chatbot_id})

async def get_chatbots_by_document_id(document_id: str) -> List[Chatbot]:
    return await chatbot_collection.find({"document.id_document": document_id}).to_list()

async def add_history_item(chatbot_id: str, question: str, answer: str) -> Optional[Chatbot]:
    history_item = HistoryItem(
        question=question,
        answer=answer
    )
    
    update_query = {
        "$push": {"history": history_item.dict()},
        "$set": {"updated_at": datetime.utcnow()}
    }
    
    chatbot = await chatbot_collection.find_one({"chatbot_id": chatbot_id})
    if not chatbot:
        return None
        
    await chatbot.update(update_query)
    return chatbot

async def get_chat_history(chatbot_id: str) -> List[HistoryItem]:
    chatbot = await chatbot_collection.find_one({"chatbot_id": chatbot_id})
    return chatbot.history if chatbot else []

async def clear_chat_history(chatbot_id: str) -> Optional[Chatbot]:
    update_query = {
        "$set": {
            "history": [],
            "updated_at": datetime.utcnow()
        }
    }
    
    chatbot = await chatbot_collection.find_one({"chatbot_id": chatbot_id})
    if not chatbot:
        return None
        
    await chatbot.update(update_query)
    return chatbot

async def delete_chatbot(chatbot_id: str) -> bool:
    chatbot = await chatbot_collection.find_one({"chatbot_id": chatbot_id})
    if chatbot:
        await chatbot.delete()
        return True
    return False 