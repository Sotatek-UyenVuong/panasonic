from fastapi import HTTPException, APIRouter
from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import HTMLResponse, StreamingResponse
import os
import json
import re
from core.chat import chat, chat_stream, chat_streamv2
from cohere import ChatbotMessage, UserMessage
import asyncio
from constants.LLM_models import ModelName, MODELS, Provider
import google.generativeai as genai
import sys
import logging

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.chatbot import get_chatbot_by_id, add_history_item
from database.page import get_pages_by_document_id

# Configure logging
logger = logging.getLogger(__name__)

# Định nghĩa model cho request
class ChatStreamRequest(BaseModel):
    query: str
    model_name: str
    chatbot_id: str

class ChatMessage(BaseModel):
    query: str
    model_name: str
    chatbot_id: str

class ChatResponse(BaseModel):
    answer: str
    images: List[dict]

# Định nghĩa router
router = APIRouter()

def get_model_enum(model_name: str) -> ModelName:
    """Convert model name string to ModelName enum."""
    try:
        # Try direct conversion
        return ModelName[model_name]
    except (KeyError, ValueError):
        # If that fails, try to find by value
        for member in ModelName:
            if member.value == model_name:
                return member
        raise ValueError(f"Invalid model name: {model_name}")

@router.post("/chat-stream")
async def chat_stream_endpoint(chat_request: ChatStreamRequest):
    try:
        # Get chatbot from database
        chatbot = await get_chatbot_by_id(chat_request.chatbot_id)
        if not chatbot:
            raise HTTPException(status_code=404, detail="Chatbot not found")
            
        # Get chat history from chatbot
        formatted_history = []
        if chatbot.history:
            for item in chatbot.history:
                formatted_history.append({"role": "user", "content": item.question})
                formatted_history.append({"role": "assistant", "content": item.answer})

        if not chat_request.model_name or chat_request.model_name == "default":
            async def generate():
                answer = ""  # Track the complete answer
                stream = chat_stream(
                    query=chat_request.query,
                    chat_history=formatted_history
                )
                
                for event in stream:
                    if event.type == "content-delta":
                        answer += event.delta.message.content.text
                        yield f"data: {json.dumps({'text': event.delta.message.content.text})}\n\n"
                        await asyncio.sleep(0.02)
                    
                    elif event.type == "message-end":
                        # Extract images from the answer
                        try:
                            images = await extract_images_from_text(answer, chatbot.document.id_document)
                        except Exception as e:
                            logger.error(f"Error extracting images: {str(e)}")
                            images = []

                        # Save chat history before ending
                        try:
                            await add_history_item(
                                chatbot_id=chat_request.chatbot_id,
                                question=chat_request.query,
                                answer=answer
                            )
                        except Exception as e:
                            logger.error(f"Error saving chat history: {str(e)}")
                            
                        yield f"data: {json.dumps({'done': True, 'answer': answer, 'images': images})}\n\n"
                        break
                
            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            async def generate():
                answer = ""  # Track the complete answer
                try:
                    # Convert model name to enum
                    model_enum = get_model_enum(chat_request.model_name)
                    
                    # Get response generator
                    response_generator = chat_streamv2(
                        query=chat_request.query,
                        document_id=chatbot.document.id_document,
                        chat_history=formatted_history,
                        model_name=model_enum.name
                    )
                    
                    # Get provider type
                    provider = MODELS[model_enum]["provider"]
                    
                    if provider == Provider.ANTHROPIC:
                        async for chunk in response_generator:
                            # Parse the JSON string from chat.py
                            if chunk:
                                try:
                                    data = json.loads(chunk)
                                    
                                    # Handle thinking events for CLAUDE_3_7_SONNET
                                    if data.get("type") == "text_delta" and data.get("text"):
                                        answer += data.get("text")
                                        yield f"data: {json.dumps({'text': data.get('text')})}\n\n"
                                    elif data.get("type") == "content_block_start":
                                        yield f"data: {json.dumps({'type': 'block_start', 'block_type': data.get('block_type')})}\n\n"
                                    elif data.get("type") == "content_block_stop":
                                        yield f"data: {json.dumps({'type': 'block_stop'})}\n\n"
                                    # Handle simple text streaming for other Claude models
                                    elif data.get("type") == "content_block_delta" and data.get("text"):
                                        answer += data.get("text")
                                        yield f"data: {json.dumps({'text': data.get('text')})}\n\n"
                                    elif data.get("type") == "error":
                                        yield f"data: {json.dumps({'error': data.get('error')})}\n\n"
                                except json.JSONDecodeError:
                                    # If not JSON, handle as raw text
                                    answer += chunk
                                    yield f"data: {json.dumps({'text': chunk})}\n\n"
                                await asyncio.sleep(0.02)
                    
                    elif provider == Provider.GOOGLE:
                        try:
                            model = genai.GenerativeModel(model_enum.value)
                            response = model.generate_content(
                                chat_request.query,
                                stream=True
                            )
                            
                            for chunk in response:
                                try:
                                    # Check if chunk has text directly
                                    if hasattr(chunk, 'text') and chunk.text:
                                        answer += chunk.text
                                        yield f"data: {json.dumps({'text': chunk.text})}\n\n"
                                    # Check if chunk has candidates
                                    elif hasattr(chunk, 'candidates') and chunk.candidates:
                                        for candidate in chunk.candidates:
                                            # Check if candidate has content with text
                                            if hasattr(candidate, 'content') and candidate.content:
                                                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                                    for part in candidate.content.parts:
                                                        if hasattr(part, 'text') and part.text:
                                                            answer += part.text
                                                            yield f"data: {json.dumps({'text': part.text})}\n\n"
                                                elif hasattr(candidate.content, 'text') and candidate.content.text:
                                                    answer += candidate.content.text
                                                    yield f"data: {json.dumps({'text': candidate.content.text})}\n\n"
                                    # Check if chunk has finish_reason
                                    elif hasattr(chunk, 'finish_reason'):
                                        if chunk.finish_reason == 1:  # SAFETY
                                            yield f"data: {json.dumps({'error': 'Content was blocked for safety reasons.'})}\n\n"
                                        elif chunk.finish_reason == 2:  # RECITATION
                                            yield f"data: {json.dumps({'error': 'Content was blocked for recitation reasons.'})}\n\n"
                                        elif chunk.finish_reason == 3:  # OTHER
                                            yield f"data: {json.dumps({'error': 'Content generation was stopped for other reasons.'})}\n\n"
                                except Exception as chunk_error:
                                    print(f"Error processing Gemini chunk: {str(chunk_error)}")
                                    # Continue to next chunk instead of breaking the stream
                                
                                await asyncio.sleep(0.02)
                            
                            # Extract images and save chat history before ending
                            try:
                                images = await extract_images_from_text(answer, chatbot.document.id_document)
                                await add_history_item(
                                    chatbot_id=chat_request.chatbot_id,
                                    question=chat_request.query,
                                    answer=answer
                                )
                                yield f"data: {json.dumps({'done': True, 'answer': answer, 'images': images})}\n\n"
                            except Exception as e:
                                logger.error(f"Error in post-processing: {str(e)}")
                                yield f"data: {json.dumps({'error': f'Error in post-processing: {str(e)}'})}\n\n"
                            
                        except Exception as e:
                            error_msg = str(e)
                            print(f"Error in Gemini stream: {error_msg}")
                            yield f"data: {json.dumps({'error': error_msg})}\n\n"
                    
                    elif provider == Provider.OPENAI:
                        try:
                            print(f"Debug - Response type: {type(response)}")
                            
                            for chunk in response:
                                try:
                                    if chunk:
                                        data = json.loads(chunk)
                                        
                                        if data.get("type") == "text_delta" and data.get("text"):
                                            answer += data.get("text")
                                            print(f"Debug - Content received: {data.get('text')}")
                                            yield f"data: {json.dumps({'text': data.get('text')})}\n\n"
                                        elif data.get("type") == "finish":
                                            print(f"Debug - Finish reason: {data.get('reason')}")
                                            if data.get("reason") == "stop":
                                                # Extract images and save chat history before ending
                                                try:
                                                    images = await extract_images_from_text(answer, chatbot.document.id_document)
                                                    await add_history_item(
                                                        chatbot_id=chat_request.chatbot_id,
                                                        question=chat_request.query,
                                                        answer=answer
                                                    )
                                                    yield f"data: {json.dumps({'done': True, 'answer': answer, 'images': images})}\n\n"
                                                except Exception as e:
                                                    logger.error(f"Error in post-processing: {str(e)}")
                                                    yield f"data: {json.dumps({'error': f'Error in post-processing: {str(e)}'})}\n\n"
                                            else:
                                                yield f"data: {json.dumps({'info': 'Stream ended: ' + str(data.get('reason'))})}\n\n"
                                        elif data.get("type") == "error":
                                            print(f"Error from OpenAI: {data.get('error')}")
                                            yield f"data: {json.dumps({'error': data.get('error')})}\n\n"
                                    
                                    await asyncio.sleep(0.02)
                                    
                                except Exception as chunk_error:
                                    print(f"Error processing chunk: {str(chunk_error)}")
                                    print(f"Chunk data: {chunk}")
                                    yield f"data: {json.dumps({'error': f'Error processing chunk: {str(chunk_error)}'})}\n\n"
                        
                        except Exception as e:
                            error_msg = str(e)
                            print(f"Error in OpenAI stream: {error_msg}")
                            yield f"data: {json.dumps({'error': error_msg})}\n\n"
                    
                    # Extract images and save chat history before ending (if not already saved)
                    if answer and provider != Provider.OPENAI and provider != Provider.GOOGLE:  # These providers already handle this
                        try:
                            images = await extract_images_from_text(answer, chatbot.document.id_document)
                            await add_history_item(
                                chatbot_id=chat_request.chatbot_id,
                                question=chat_request.query,
                                answer=answer
                            )
                            yield f"data: {json.dumps({'done': True, 'answer': answer, 'images': images})}\n\n"
                        except Exception as e:
                            logger.error(f"Error in post-processing: {str(e)}")
                            yield f"data: {json.dumps({'error': f'Error in post-processing: {str(e)}'})}\n\n"
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"Error in generate: {error_msg}")
                    yield f"data: {json.dumps({'error': error_msg})}\n\n"
                    
            return StreamingResponse(generate(), media_type="text/event-stream")
            
    except Exception as e:
        error_msg = str(e)
        print(f"Error in chat_stream_endpoint: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/chat-streamv2", response_model=ChatResponse)
async def chat_stream_v2_endpoint(chat_request: ChatMessage):
    try:
        # Get chatbot from database
        chatbot = await get_chatbot_by_id(chat_request.chatbot_id)
        if not chatbot:
            raise HTTPException(status_code=404, detail="Chatbot not found")
            
        # Get chat history from chatbot
        formatted_history = []
        if chatbot.history:  # Add null check
            for item in chatbot.history:
                formatted_history.append({"role": "user", "content": item.question})
                formatted_history.append({"role": "assistant", "content": item.answer})

        # Initialize response variables
        answer = ""
        
        async def generate():
            nonlocal answer
            try:
                # Get response generator
                response_generator = chat_streamv2(
                    query=chat_request.query,
                    document_id=chatbot.document.id_document,
                    chat_history=formatted_history,
                    model_name=chat_request.model_name
                )
                
                if response_generator is None:
                    logger.error("Chat stream returned None")
                    yield f"data: {json.dumps({'error': 'Chat stream initialization failed'})}\n\n"
                    return

                async for chunk in response_generator:
                    if chunk:
                        try:
                            data = json.loads(chunk)
                            
                            if data.get("type") == "text_delta" and data.get("text"):
                                answer += data.get("text")
                                yield f"data: {json.dumps({'text': data.get('text')})}\n\n"
                            elif data.get("type") == "content_block_start":
                                yield f"data: {json.dumps({'type': 'block_start', 'block_type': data.get('block_type')})}\n\n"
                            elif data.get("type") == "content_block_stop":
                                yield f"data: {json.dumps({'type': 'block_stop'})}\n\n"
                            elif data.get("type") == "content_block_delta" and data.get("text"):
                                answer += data.get("text")
                                yield f"data: {json.dumps({'text': data.get('text')})}\n\n"
                            elif data.get("type") == "error":
                                logger.error(f"Error from chat stream: {data.get('error')}")
                                yield f"data: {json.dumps({'error': data.get('error')})}\n\n"
                                return
                        except json.JSONDecodeError:
                            answer += chunk
                            yield f"data: {json.dumps({'text': chunk})}\n\n"
                        await asyncio.sleep(0.02)
                
                if answer:
                    try:
                        # Extract images from the answer
                        images = await extract_images_from_text(answer, chatbot.document.id_document)
                        
                        # Save chat history
                        await add_history_item(
                            chatbot_id=chat_request.chatbot_id,
                            question=chat_request.query,
                            answer=answer
                        )
                        
                        # Return final response
                        yield f"data: {json.dumps({'done': True, 'answer': answer, 'images': images})}\n\n"
                    except Exception as e:
                        logger.error(f"Error in post-processing: {str(e)}")
                        yield f"data: {json.dumps({'error': f'Error in post-processing: {str(e)}'})}\n\n"
                else:
                    logger.error("No answer generated from chat stream")
                    yield f"data: {json.dumps({'error': 'No response generated'})}\n\n"
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error in generate: {error_msg}")
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
            
        return StreamingResponse(generate(), media_type="text/event-stream")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in chat_stream_endpoint: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/image/{chatbot_id}/{image_id}")
async def get_image(chatbot_id: str, image_id: str):
    try:
        # Get chatbot from database
        chatbot = await get_chatbot_by_id(chatbot_id)
        if not chatbot:
            raise HTTPException(status_code=404, detail="Chatbot not found")
            
        # Get all pages for this document
        pages = await get_pages_by_document_id(chatbot.document.id_document)
        if not pages:
            raise HTTPException(status_code=404, detail="No pages found for document")
            
        # Look for the image in all pages
        for page in pages:
            if page.images:
                for img in page.images:
                    # Try both with and without file extension
                    if img.id == image_id or img.id.split('.')[0] == image_id:
                        return {"image_b64": img.image_b64}
                        
        raise HTTPException(status_code=404, detail=f"Image {image_id} not found")
        
    except Exception as e:
        logger.error(f"Error getting image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def extract_images_from_text(text: str, document_id: str) -> List[dict]:
    """Extract image information from text and fetch from database."""
    images = []
    # Pattern to match markdown image syntax: ![img-2.jpeg](img-2.jpeg)
    image_pattern = r'!\[(.*?)\]\((.*?)\)'
    
    try:
        # Get all pages for this document
        pages = await get_pages_by_document_id(document_id)
        if not pages:
            logger.warning(f"No pages found for document {document_id}")
            return []
            
        # Create a map of page images for faster lookup
        page_images_map = {}
        for page in pages:
            if page.images:
                for img in page.images:
                    # Remove file extension if present in the id
                    clean_id = img.id.split('.')[0]
                    page_images_map[clean_id] = img
                    # Also store with extension for direct matches
                    page_images_map[img.id] = img
        
        # Find all image matches in text
        matches = re.finditer(image_pattern, text)
        
        # Process each image match
        for match in matches:
            image_ref = match.group(1)  # e.g. img-2.jpeg
            image_name = match.group(2)  # e.g. img-2.jpeg
            
            # Try different variations of the image id
            image_id = image_ref.split('.')[0]  # e.g. img-2
            
            # Look up image in our map
            if image_id in page_images_map:
                img = page_images_map[image_id]
                images.append({
                    "id": img.id,
                    "image_b64": img.image_b64
                })
                logger.info(f"Found image {image_id} in document {document_id}")
            else:
                logger.warning(f"Image {image_id} not found in document {document_id}")
        
        return images
        
    except Exception as e:
        logger.error(f"Error extracting images: {str(e)}")
        return []