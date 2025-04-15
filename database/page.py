from typing import List, Optional
from datetime import datetime
import sys
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collection_db.page import Page, Image


page_collection = Page

async def create_page(
    document_id: str,
    page_id: str,
    page_number: int,
    markdown: str,
    images: List[Image] = None
) -> Page:
    try:
        logger.info(f"Creating page with ID: {page_id}")
        page = Page(
            document_id=document_id,
            page_id=page_id,
            page_number=page_number,
            markdown=markdown,
            images=images or []
        )
        created_page = await page_collection.create(page)
        if not created_page:
            logger.error(f"Failed to create page {page_id}")
            return None
        logger.info(f"Successfully created page {page_id}")
        return created_page
    except Exception as e:
        logger.error(f"Error creating page: {str(e)}", exc_info=True)
        return None

async def get_page_by_id(page_id: str) -> Optional[Page]:
    return await page_collection.find_one({"page_id": page_id})

async def get_pages_by_document_id(document_id: str) -> List[Page]:
    return await page_collection.find({"document_id": document_id}).sort("page_number").to_list()

async def get_all_pages() -> List[Page]:
    return await page_collection.find_all().to_list()

async def update_page(
    page_id: str,
    markdown: str = None,
    images: List[Image] = None
) -> Optional[Page]:
    update_query = {"$set": {"updated_at": datetime.utcnow()}}
    
    if markdown is not None:
        update_query["$set"]["markdown"] = markdown
    if images is not None:
        update_query["$set"]["images"] = images
    
    page = await page_collection.find_one({"page_id": page_id})
    if not page:
        return None
        
    await page.update(update_query)
    return page

async def add_image_to_page(page_id: str, image: Image) -> Optional[Page]:
    update_query = {
        "$push": {"images": image.dict()},
        "$set": {"updated_at": datetime.utcnow()}
    }
    
    page = await page_collection.find_one({"page_id": page_id})
    if not page:
        return None
        
    await page.update(update_query)
    return page

async def delete_page(page_id: str) -> bool:
    page = await page_collection.find_one({"page_id": page_id})
    if page:
        await page.delete()
        return True
    return False

async def delete_pages_by_document_id(document_id: str) -> int:
    result = await page_collection.find({"document_id": document_id}).delete()
    return result.deleted_count 