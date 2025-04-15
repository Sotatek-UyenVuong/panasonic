from cohere import Client, ClientV2
from cohere import ChatbotMessage, UserMessage
import json
import os
from dotenv import load_dotenv
from core.load_documents import load_documents
from core.prompt import PROMPT_CHAT_SYSTEM
from core.retrieve import retrieve_and_rerank, load_vector_database
from LLM.router import LLM_router
from llama_index.core.llms import ChatMessage, MessageRole
from constants.LLM_models import Provider, MODELS, ModelName
from openai import OpenAI
import time

load_dotenv()

API_KEY = os.getenv("COHERE_API_KEY")

chunks, embeddings = load_vector_database()

def chat(message, chat_history=None, model="command-r-plus-04-2024"):
    client = Client(api_key=API_KEY)
    
    if chat_history is None:
        chat_history = []
    
    response = client.chat(
        message=message,
        model=model,
        preamble=PROMPT_CHAT_SYSTEM,
        chat_history=chat_history,
        documents=load_documents()
    )
    
    return response

def chat_stream(query, chat_history=None, model="command-r-plus-04-2024"):
    co = ClientV2(api_key=API_KEY)
    
    message = [{"role": "system", "content": PROMPT_CHAT_SYSTEM}]
    
    if chat_history is None:
        chat_history = []
    else:
        message = message + chat_history
        
    messages = message + [{"role": "user", "content": query}]
    
    results = retrieve_and_rerank(query, chunks, embeddings)
    
    documents = []
    for idx, result in enumerate(results):
        documents.append(
            {
                "data":
                {
                    "title": f"chunk_ {idx + 1}",
                    "snippet": result[0]
                }
            }
        )
    
    stream = co.chat_stream(
        messages=messages,
        model=model,
        documents=documents
    )
    
    return stream

def chat_streamv2(query, chat_history=None, model_name="CLAUDE_3_7_SONNET", temperature=0.0):
    try:
        # Get provider and model config
        model_enum = ModelName[model_name]  # Convert string to enum using name
        provider = MODELS[model_enum]["provider"]
        model_config = MODELS[model_enum]["override_params"].copy()
        
        # Format chat history into messages, filtering out empty messages
        formatted_messages = []
        if chat_history:
            for msg in chat_history:
                if msg.get("content") and msg["content"].strip():  # Only add messages with non-empty content
                    role = "user" if msg["role"] == "user" else "assistant"
                    formatted_messages.append({"role": role, "content": msg["content"].strip()})
        
        # Create system and user messages
        system_prompt = PROMPT_CHAT_SYSTEM
        
        # Try to get context if possible, but don't require it
        context_str = "[]"
        try:
            if chunks is not None and embeddings is not None:
                results = retrieve_and_rerank(query, chunks, embeddings)
                if results:
                    documents = [{"title": f"chunk_{idx + 1}", "content": result[0]} 
                               for idx, result in enumerate(results)]
                    context_str = json.dumps(documents, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not retrieve context: {str(e)}")
            # Continue without context
        
        # Construct user prompt with or without context
        user_prompt = query
        if context_str != "[]":
            user_prompt = f"""Documents: {context_str}

Question: {query}

Please provide a detailed answer based on the documents above.""".strip()

        try:
            # Get appropriate client based on provider
            llm_router = LLM_router(model_name=model_name, temperature=temperature)
            client = llm_router.get_model()

            if provider == Provider.ANTHROPIC:
                messages = [
                    *formatted_messages,
                    {"role": "user", "content": user_prompt}
                ]
                
                # Kiểm tra API key
                api_key = MODELS[model_enum]["api_key"]
                if not api_key:
                    print("Missing API key for Anthropic model")
                    yield json.dumps({
                        "type": "error",
                        "error": "Missing API key for Anthropic model"
                    })
                    return
                
                print(f"Using Anthropic API key: {api_key[:5]}...")
                
                try:
                    from anthropic import Anthropic
                    # Tạo client mới với API key
                    anthropic_client = Anthropic(api_key=api_key)
                    
                    # Special handling for CLAUDE_3_7_SONNET with thinking feature
                    if model_name == "CLAUDE_3_7_SONNET":
                        max_retries = 3
                        retry_delay = 2  # Initial delay in seconds
                        
                        for retry in range(max_retries):
                            try:
                                with anthropic_client.messages.stream(
                                    model=model_enum.value,
                                    messages=messages,
                                    system=system_prompt,  # Add system prompt as top-level parameter
                                    max_tokens=32000,
                                    temperature=1.0
                                ) as stream:
                                    for event in stream:
                                        if event.type == "content_block_start":
                                            yield json.dumps({
                                                "type": "content_block_start",
                                                "block_type": event.content_block.type
                                            })
                                        elif event.type == "content_block_delta":
                                            if event.delta.type == "thinking_delta":
                                                yield json.dumps({
                                                    "type": "thinking_delta",
                                                    "text": event.delta.thinking
                                                })
                                            elif event.delta.type == "text_delta":
                                                yield json.dumps({
                                                    "type": "text_delta",
                                                    "text": event.delta.text
                                                })
                                        elif event.type == "content_block_stop":
                                            yield json.dumps({
                                                "type": "content_block_stop"
                                            })
                                # If we get here, the stream completed successfully
                                break
                            except Exception as e:
                                error_str = str(e)
                                print(f"Error in Anthropic API call (attempt {retry+1}/{max_retries}): {error_str}")
                                
                                # Check if it's an overloaded error
                                if "overloaded" in error_str.lower():
                                    if retry < max_retries - 1:
                                        # Calculate exponential backoff
                                        wait_time = retry_delay * (2 ** retry)
                                        print(f"API overloaded. Retrying in {wait_time} seconds...")
                                        yield json.dumps({
                                            "type": "info",
                                            "text": f"API overloaded. Retrying in {wait_time} seconds..."
                                        })
                                        time.sleep(wait_time)
                                    else:
                                        # Max retries reached
                                        yield json.dumps({
                                            "type": "error",
                                            "error": "Anthropic API is currently overloaded. Please try again later."
                                        })
                                        return
                                else:
                                    # For other errors, just yield the error
                                    yield json.dumps({
                                        "type": "error",
                                        "error": error_str
                                    })
                                    return
                    # Simple streaming for other Claude models
                    else:
                        with anthropic_client.messages.stream(
                            model=model_enum.value,
                            messages=messages,
                            system=system_prompt,  # Add system prompt as top-level parameter
                            max_tokens=model_config.get("max_tokens", 4096),
                            temperature=temperature
                        ) as stream:
                            for text in stream.text_stream:
                                yield json.dumps({
                                    "type": "content_block_delta",
                                    "text": text
                                })
                            
                except Exception as e:
                    print(f"Error in Anthropic API call: {str(e)}")
                    yield json.dumps({
                        "type": "error",
                        "error": f"Anthropic API error: {str(e)}"
                    })
                return

            elif provider == Provider.GOOGLE:
                # Format messages for Gemini with system prompt
                formatted_prompt = f"System: {system_prompt}\n\n"
                for msg in formatted_messages:
                    formatted_prompt += f"{msg['role'].title()}: {msg['content']}\n\n"
                formatted_prompt += f"User: {user_prompt}\n\nAssistant: "
                
                model = client.GenerativeModel(model_enum.value)
                response = model.generate_content(
                    formatted_prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": model_config.get("max_tokens", 4096)
                    },
                    stream=True
                )
                
                for chunk in response:
                    if chunk.text:
                        yield json.dumps({
                            "type": "text_delta",
                            "text": chunk.text
                        })

            elif provider == Provider.OPENAI:
                try:
                    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                    
                    messages = [
                        {"role": "system", "content": system_prompt},
                        *formatted_messages,
                        {"role": "user", "content": user_prompt}
                    ]
                    
                    print("OpenAI messages:", messages)
                    
                    stream = client.chat.completions.create(
                        model=model_enum.value,
                        messages=messages,
                        stream=True,
                        temperature=temperature,
                        max_tokens=model_config.get("max_tokens", 4096)
                    )
                    
                    for chunk in stream:
                        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                            yield json.dumps({
                                "type": "text_delta",
                                "text": chunk.choices[0].delta.content
                            })
                        elif chunk.choices and chunk.choices[0].finish_reason:
                            yield json.dumps({
                                "type": "finish",
                                "reason": chunk.choices[0].finish_reason
                            })
                            
                except Exception as e:
                    print(f"Error creating OpenAI stream: {str(e)}")
                    yield json.dumps({
                        "type": "error",
                        "error": f"OpenAI API error: {str(e)}"
                    })

            else:
                raise ValueError(f"Unsupported provider: {provider}")

        except Exception as e:
            print(f"Error in chat_streamv2: {str(e)}")
            raise

    except KeyError as e:
        print(f"Invalid model name: {model_name}")
        raise ValueError(f"Invalid model name: {model_name}")
    except Exception as e:
        print(f"Error in chat_streamv2: {str(e)}")
        raise