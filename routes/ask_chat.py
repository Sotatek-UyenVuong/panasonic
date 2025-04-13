from fastapi import HTTPException, APIRouter
from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import HTMLResponse, StreamingResponse
import os
import json
from core.chat import chat, chat_stream, chat_streamv2
from cohere import ChatbotMessage, UserMessage
import asyncio
from constants.LLM_models import ModelName, MODELS, Provider
import google.generativeai as genai


# Định nghĩa model cho request
class ChatMessage(BaseModel):
    message: str
    chat_history: Optional[List[dict]] = None
    model: Optional[str] = None

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

@router.post("/chat")
async def chat_endpoint(chat_request: ChatMessage):
    try:
        formatted_history = []
        if chat_request.chat_history:
            for msg in chat_request.chat_history:
                if msg.get("role") == "user":
                    formatted_history.append({"role": "user", "content": msg.get("message")})
                elif msg.get("role") == "assistant" and msg.get("message") != "Hello! I'm RaidenX's assistant. How can I help you with today?":
                    formatted_history.append({"role": "assistant", "content": msg.get("message")})
        
        response = chat(
            message=chat_request.message,
            chat_history=formatted_history
        )
        
        return {
            "response": response.text,
            "citations": response.citations,
            "images": response.images,
            "documents": response.documents
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat-stream")
async def chat_stream_endpoint(chat_request: ChatMessage):
    try:
        formatted_history = []
        if chat_request.chat_history:
            for msg in chat_request.chat_history:
                if msg.get("role") == "user":
                    formatted_history.append({"role": "user", "content": msg.get("message")})
                else:
                    formatted_history.append({"role": "assistant", "content": msg.get("message")})

        if not chat_request.model or chat_request.model == "default":
            async def generate():
                stream = chat_stream(
                    query=chat_request.message,
                    chat_history=formatted_history
                )
                
                for event in stream:
                    if event.type == "content-delta":
                        yield f"data: {json.dumps({'text': event.delta.message.content.text})}\n\n"
                        await asyncio.sleep(0.02)
                    
                    elif event.type == "message-end":
                        yield f"data: {json.dumps({'done': True})}\n\n"
                        break
                
            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            async def generate():
                try:
                    # Convert model name to enum
                    model_enum = get_model_enum(chat_request.model)
                    
                    response = chat_streamv2(
                        query=chat_request.message,
                        chat_history=formatted_history,
                        model_name=model_enum.name
                    )
                    
                    # Get provider type
                    provider = MODELS[model_enum]["provider"]
                    
                    if provider == Provider.ANTHROPIC:
                        for chunk in response:
                            # Parse the JSON string from chat.py
                            if chunk:
                                try:
                                    data = json.loads(chunk)
                                    
                                    # Handle thinking events for CLAUDE_3_7_SONNET
                                    if data.get("type") == "text_delta" and data.get("text"):
                                        yield f"data: {json.dumps({'text': data.get('text')})}\n\n"
                                    elif data.get("type") == "content_block_start":
                                        yield f"data: {json.dumps({'type': 'block_start', 'block_type': data.get('block_type')})}\n\n"
                                    elif data.get("type") == "content_block_stop":
                                        yield f"data: {json.dumps({'type': 'block_stop'})}\n\n"
                                    # Handle simple text streaming for other Claude models
                                    elif data.get("type") == "content_block_delta" and data.get("text"):
                                        yield f"data: {json.dumps({'text': data.get('text')})}\n\n"
                                    elif data.get("type") == "error":
                                        yield f"data: {json.dumps({'error': data.get('error')})}\n\n"
                                except json.JSONDecodeError:
                                    # If not JSON, handle as raw text
                                    yield f"data: {json.dumps({'text': chunk})}\n\n"
                                await asyncio.sleep(0.02)
                    
                    elif provider == Provider.GOOGLE:
                        try:
                            model = genai.GenerativeModel(model_enum.value)
                            response = model.generate_content(
                                chat_request.message,
                                stream=True
                            )
                            
                            for chunk in response:
                                try:
                                    # Check if chunk has text directly
                                    if hasattr(chunk, 'text') and chunk.text:
                                        yield f"data: {json.dumps({'text': chunk.text})}\n\n"
                                    # Check if chunk has candidates
                                    elif hasattr(chunk, 'candidates') and chunk.candidates:
                                        for candidate in chunk.candidates:
                                            # Check if candidate has content with text
                                            if hasattr(candidate, 'content') and candidate.content:
                                                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                                    for part in candidate.content.parts:
                                                        if hasattr(part, 'text') and part.text:
                                                            yield f"data: {json.dumps({'text': part.text})}\n\n"
                                                elif hasattr(candidate.content, 'text') and candidate.content.text:
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
                            
                            yield f"data: {json.dumps({'done': True})}\n\n"
                            
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
                                            print(f"Debug - Content received: {data.get('text')}")
                                            yield f"data: {json.dumps({'text': data.get('text')})}\n\n"
                                        elif data.get("type") == "finish":
                                            print(f"Debug - Finish reason: {data.get('reason')}")
                                            if data.get("reason") == "stop":
                                                yield f"data: {json.dumps({'done': True})}\n\n"
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
                    
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"Error in generate: {error_msg}")
                    yield f"data: {json.dumps({'error': error_msg})}\n\n"
                    
            return StreamingResponse(generate(), media_type="text/event-stream")
            
    except Exception as e:
        error_msg = str(e)
        print(f"Error in chat_stream_endpoint: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/chat-streamv2")
async def chat_stream_v2_endpoint(chat_request: ChatMessage, model: str = "CLAUDE_3_7_SONNET"):
    try:
        formatted_history = []
        if chat_request.chat_history:
            for msg in chat_request.chat_history:
                if msg.get("role") == "user":
                    formatted_history.append({"role": "user", "content": msg.get("message")})
                else:
                    formatted_history.append({"role": "assistant", "content": msg.get("message")})

        async def generate():
            try:
                # Convert model name to enum
                model_enum = get_model_enum(model)
                
                stream = chat_streamv2(
                    query=chat_request.message,
                    chat_history=formatted_history,
                    model_name=model_enum.name
                )
                
                # Check if model is Claude to handle properly
                provider = MODELS[model_enum]["provider"]
                
                if provider == Provider.ANTHROPIC:
                    for chunk in stream:
                        # Parse the JSON string from chat.py
                        if chunk:
                            try:
                                data = json.loads(chunk)
                                
                                # Handle thinking events for CLAUDE_3_7_SONNET
                                if data.get("type") == "text_delta" and data.get("text"):
                                    yield f"data: {json.dumps({'text': data.get('text')})}\n\n"
                                elif data.get("type") == "content_block_start":
                                    yield f"data: {json.dumps({'type': 'block_start', 'block_type': data.get('block_type')})}\n\n"
                                elif data.get("type") == "content_block_stop":
                                    yield f"data: {json.dumps({'type': 'block_stop'})}\n\n"
                                # Handle simple text streaming for other Claude models
                                elif data.get("type") == "content_block_delta" and data.get("text"):
                                    yield f"data: {json.dumps({'text': data.get('text')})}\n\n"
                                elif data.get("type") == "error":
                                    yield f"data: {json.dumps({'error': data.get('error')})}\n\n"
                            except json.JSONDecodeError:
                                # If not JSON, handle as raw text
                                yield f"data: {json.dumps({'text': chunk})}\n\n"
                            await asyncio.sleep(0.02)
                else:
                    # Handle other models
                    for chunk in stream:
                        if hasattr(chunk, 'text') and chunk.text:
                            yield f"data: {json.dumps({'text': chunk.text})}\n\n"
                        await asyncio.sleep(0.02)
                
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                error_msg = str(e)
                print(f"Error in generate: {error_msg}")
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
            
        return StreamingResponse(generate(), media_type="text/event-stream")
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in chat_stream_endpoint: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

    try:
        formatted_history = []
        if chat_request.chat_history:
            for msg in chat_request.chat_history:
                if msg.get("role") == "user":
                    formatted_history.append({"role": "user", "content": msg.get("message")})
                else:
                    formatted_history.append({"role": "assistant", "content": msg.get("message")})

        async def generate():
            try:
                # Run the ReAct Agent
                response = run_react_agent(
                    query=chat_request.message,
                    chat_history=formatted_history
                )
                
                # Process the response
                for chunk in response:
                    if chunk:
                        try:
                            data = json.loads(chunk)
                            
                            # Handle text delta
                            if data.get("type") == "text_delta" and data.get("text"):
                                yield f"data: {json.dumps({'text': data.get('text')})}\n\n"
                            
                            # Handle done message
                            elif data.get("type") == "done":
                                yield f"data: {json.dumps({'done': True})}\n\n"
                            
                            # Handle error
                            elif data.get("type") == "error":
                                yield f"data: {json.dumps({'error': data.get('error')})}\n\n"
                        
                        except json.JSONDecodeError:
                            # If not JSON, handle as raw text
                            yield f"data: {json.dumps({'text': chunk})}\n\n"
                        
                        await asyncio.sleep(0.02)
                
            except Exception as e:
                error_msg = str(e)
                print(f"Error in ReAct Agent: {error_msg}")
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in chat_stream_agent_endpoint: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)