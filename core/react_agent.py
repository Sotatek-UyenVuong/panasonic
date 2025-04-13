import os
from dotenv import load_dotenv
import json
from typing import List, Dict, Any, Generator, Optional

from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.llms.openai import OpenAI
from retrieve import retrieve_and_rerank, load_vector_database

# Load environment variables
load_dotenv()

# Define LLM factory function for consistent model usage
def get_llm(model_name: str = "gpt-4o-mini") -> OpenAI:
    """Create an OpenAI LLM instance with the specified model."""
    return OpenAI(model=model_name, api_key=os.getenv("OPENAI_API_KEY"))

# Tool functions
def search_documents(query: str, k: int = 10) -> List[Dict[str, Any]]:
    """
    Search for relevant documents based on the query.
    
    Args:
        query: The search query
        k: Number of results to return
        
    Returns:
        List of relevant document chunks with their relevance scores
    """
    # Load vector database if not already loaded
    chunks, embeddings = load_vector_database()
    results = retrieve_and_rerank(query, chunks, embeddings, k=k)
    return [{"content": result[0], "score": result[1]} for result in results]

def evaluate_information(info: str, query: str) -> Dict[str, Any]:
    """
    Evaluate the relevance, accuracy, and completeness of information for the query.
    
    Args:
        info: The information to evaluate
        query: The original query
        
    Returns:
        Dictionary with evaluation results
    """
    llm = get_llm()
    
    prompt = f"""
    Evaluate the following information in relation to the query:
    
    Query: {query}
    
    Information: {info}
    
    Provide an evaluation in JSON format with the following fields:
    - relevance_score (0.0-1.0): How relevant the information is to the query
    - is_relevant (boolean): Whether the information is relevant
    - information_completeness (0.0-1.0): How complete the information is for answering the query
    - is_complete (boolean): Whether the information is complete enough to answer the query
    - missing_aspects (array): List of aspects from the query that are not addressed in the information
    - confidence (string): "low", "medium", or "high"
    - evaluation (string): Brief evaluation of the information
    """
    
    response = llm.complete(prompt)
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        # Fallback in case LLM doesn't return valid JSON
        return {
            "relevance_score": 0.5,
            "is_relevant": True,
            "information_completeness": 0.5,
            "is_complete": False,
            "missing_aspects": ["Details not specified"],
            "confidence": "medium",
            "evaluation": "The information is partially relevant but may not be complete."
        }

def check_information_completeness(query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check if the search results contain enough information to answer the query.
    
    Args:
        query: The original query
        search_results: The results from the search tool
        
    Returns:
        Dictionary with assessment of completeness
    """
    # Extract content from search results
    contents = [result["content"] for result in search_results]
    combined_content = "\n\n".join(contents)
    
    llm = get_llm()
    
    prompt = f"""
    Determine if the following information is sufficient to answer the query:
    
    Query: {query}
    
    Information:
    {combined_content}
    
    Return a JSON with the following structure:
    - "is_sufficient": true/false
    - "missing_information": [list of specific pieces of missing information]
    - "can_answer_partially": true/false
    - "recommendation": "answer", "clarify", or "search_more"
    """
    
    response = llm.complete(prompt)
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        return {
            "is_sufficient": False,
            "missing_information": ["Unable to determine specific missing information"],
            "can_answer_partially": False,
            "recommendation": "clarify"
        }

def clarify_question(query: str, context: str = "", search_results: List[Dict[str, Any]] = None, user_responses: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Determine if clarification is needed and generate clarifying questions.
    
    Args:
        query: The original query
        context: Any existing context (default empty string)
        search_results: Results from previous searches (optional)
        user_responses: Dictionary of previous clarifying Q&A (optional)
        
    Returns:
        Dictionary with clarification information
    """
    llm = get_llm()
    
    # Build comprehensive context from search results if available
    full_context = context
    if search_results:
        search_content = "\n".join(f"- {result['content']}" for result in search_results)
        full_context += f"\nSearch Results:\n{search_content}"
    
    # Add user responses to context if available
    if user_responses:
        responses_content = "\n".join(f"Q: {q}\nA: {a}" for q, a in user_responses.items())
        full_context += f"\nPrevious Clarifications:\n{responses_content}"
    
    prompt = f"""
    Given the following query and the context retrieved, determine if more information is needed:
    
    Query: {query}
    
    Context: {full_context}
    
    Instructions:
    1. Consider all available information including search results and previous clarifications
    2. Analyze if the combined context contains sufficient information to answer the query
    3. If information is insufficient, generate specific clarifying questions
    4. Avoid asking questions that have already been answered in previous clarifications
    5. Return a JSON with the following structure:
       - "needs_clarification": true/false
       - "clarifying_questions": [list of questions if needed]
       - "explanation": reason for needing clarification or not
    """
    
    response = llm.complete(prompt)
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        # Fallback in case LLM doesn't return valid JSON
        return {
            "needs_clarification": True,
            "clarifying_questions": ["Could you provide more details about your question?"],
            "explanation": "Unable to determine if context is sufficient, requesting clarification."
        }

def synthesize_answer(query: str, context: str, clarifications: Optional[Dict[str, Any]] = None) -> str:
    """
    Synthesize a final answer based on the query, context, and any clarifications.
    
    Args:
        query: The original query
        context: The current context (retrieved information)
        clarifications: Any clarifications received from the user
        
    Returns:
        The synthesized answer
    """
    llm = get_llm()
    
    # Format any clarifications provided
    clarification_text = ""
    if clarifications and isinstance(clarifications, dict):
        if "user_responses" in clarifications and clarifications["user_responses"]:
            clarification_text = "Additional clarifications from user:\n"
            for q, a in clarifications["user_responses"].items():
                clarification_text += f"Q: {q}\nA: {a}\n\n"
    
    prompt = f"""
    Create a comprehensive answer to the user's query based on the provided information.
    
    Original Query: {query}
    
    Context Information: 
    {context}
    
    {clarification_text}
    
    Instructions for synthesizing the answer:
    1. Address all aspects of the original query directly and completely
    2. Use only information found in the provided context or clarifications
    3. If some aspects cannot be answered with the available information, acknowledge this limitation
    4. Organize the answer in a logical, easy-to-follow structure
    5. Use natural, conversational language appropriate for a help desk response
    6. Include specific references to the Panasonic manual where applicable
    7. If technical instructions are involved, present them in clear step-by-step format
    8. Keep the answer concise while being thorough

    Your final answer:
    """
    
    response = llm.complete(prompt)
    
    # Add a disclaimer if context is missing
    if not context or context.strip() == "":
        return (
            "I don't have enough information in the manual to answer this question confidently. "
            "Could you provide more details about your Panasonic device or rephrase your question?"
        )
    
    # Check if the answer seems incomplete or too short
    if len(response.text.strip()) < 50:
        return (
            f"{response.text}\n\nNote: The available information may be limited. "
            f"If this doesn't fully address your question about '{query}', "
            f"please let me know if you'd like me to search for more specific information."
        )
    
    return response.text

# Define constant for the ReAct Agent system prompt
REACT_SYSTEM_PROMPT = """
You are a helpful assistant designed to answer questions about Panasonic computer manuals.
You use a ReAct (Reasoning and Acting) approach to solve problems:

1. First, you search for relevant information in the documents.
2. Then, you evaluate the information to determine its relevance and accuracy.
3. IMPORTANT: After evaluation, explicitly check if the information is sufficient to answer the query:
   - If information is incomplete or ambiguous, use the clarify_question tool.
   - If search results don't provide enough context about specific aspects mentioned in the query, ask for clarification.
4. Only after you have sufficient information, synthesize a comprehensive answer.

When determining if clarification is needed, consider:
- Are there specific details mentioned in the query that aren't addressed in the search results?
- Is there ambiguity in the query that could lead to multiple interpretations?
- Do the search results contain contradictory information?
- If the query involves a multi-step process, do you have information for all steps?

Always be helpful, accurate, and concise in your responses.
"""

def create_react_agent(model_name: str = "gpt-4o-mini"):
    """
    Create a ReAct Agent with the specified model.
    
    Args:
        model_name: The name of the model to use
        
    Returns:
        A ReAct Agent instance
    """
    # Create function tools
    tools = [
        FunctionTool.from_defaults(fn=search_documents, name="search_documents",
                                 description="Search for relevant documents based on the query"),
        FunctionTool.from_defaults(fn=evaluate_information, name="evaluate_information",
                                 description="Evaluate the relevance and accuracy of information for the query"),
        FunctionTool.from_defaults(fn=check_information_completeness, name="check_information_completeness",
                                 description="Check if the search results contain enough information to answer the query"),
        FunctionTool.from_defaults(fn=clarify_question, name="clarify_question",
                                 description="Determine if clarification is needed and generate clarifying questions"),
        FunctionTool.from_defaults(fn=synthesize_answer, name="synthesize_answer",
                                 description="Synthesize a final answer based on the query, context, and any clarifications"),
    ]
    
    # Create the agent with configuration
    agent = ReActAgent.from_tools(
        tools=tools,
        llm=get_llm(model_name),
        system_prompt=REACT_SYSTEM_PROMPT,
        max_iterations=5,  # Limit maximum iterations
        verbose=True  # Enable verbose mode for debugging
    )
    
    return agent

def run_react_agent(query: str) -> Generator[str, None, None]:
    """
    Run the ReAct Agent on a query and yield the results.
    
    Args:
        query: The query to process
        
    Returns:
        A generator that yields the agent's responses
    """
    try:
        # Create the agent
        agent = create_react_agent()
        
        # Track search results and user responses across iterations
        search_results = []
        user_responses = {}
        
        # First, try to get relevant documents
        search_response = search_documents(query)
        if search_response:
            search_results.extend(search_response)
        
        # Check if we need clarification
        clarification_check = clarify_question(
            query=query,
            context="",
            search_results=search_results,
            user_responses=user_responses
        )
        
        if clarification_check["needs_clarification"]:
            # Yield clarifying questions
            yield json.dumps({
                "type": "clarification_needed",
                "questions": clarification_check["clarifying_questions"],
                "explanation": clarification_check["explanation"]
            })
            
            # Note: In a real implementation, you would need to handle receiving
            # user responses to these questions and update user_responses accordingly
        
        # Run the agent and get response
        response = agent.chat(query)
        
        # Yield the response
        yield json.dumps({
            "type": "text_delta",
            "text": str(response)
        })
        
    except ValueError as e:
        if "Reached max iterations" in str(e):
            error_message = "Xin lỗi, tôi đang gặp khó khăn trong việc xử lý yêu cầu của bạn. Vui lòng thử hỏi theo cách khác."
            yield json.dumps({
                "type": "error",
                "error": error_message
            })
        else:
            yield json.dumps({
                "type": "error",
                "error": str(e)
            })
    except Exception as e:
        yield json.dumps({
            "type": "error",
            "error": f"Đã xảy ra lỗi không mong muốn: {str(e)}"
        })
    finally:
        yield json.dumps({
            "type": "done",
            "done": True
        })

def continuous_chat():
    """
    Run a continuous chat session with history management.
    """
    chat_history: List[Dict[str, str]] = []
    
    print("Chào mừng bạn đến với Panasonic Assistant! (Gõ 'quit' để thoát)")
    
    while True:
        # Get user input
        user_query = input("\nCâu hỏi của bạn: ").strip()
        
        # Check for exit condition
        if user_query.lower() == 'quit':
            print("Cảm ơn bạn đã sử dụng Panasonic Assistant!")
            break
            
        # Skip empty queries
        if not user_query:
            print("Vui lòng nhập câu hỏi.")
            continue
        
        # Add user message to chat history
        chat_history.append({
            "role": "user",
            "message": user_query
        })
        
        # Get response stream
        chat_stream = run_react_agent(user_query)
        
        # Process the stream
        assistant_response = ""
        
        for response in chat_stream:
            response_obj = json.loads(response)
            
            if response_obj["type"] == "text_delta":
                # Display and collect text updates
                print(response_obj["text"], end="")
                assistant_response += response_obj["text"]
                
            elif response_obj["type"] == "error":
                # Handle errors
                error_msg = response_obj["error"]
                print(f"\nLỗi: {error_msg}")
                assistant_response = f"Lỗi: {error_msg}"
                
            elif response_obj["type"] == "done":
                # Add newline after response
                if assistant_response:
                    print("\n")
        
        # Add assistant's response to chat history
        if assistant_response:
            chat_history.append({
                "role": "assistant",
                "message": assistant_response
            })

# Start the continuous chat if running as main
if __name__ == "__main__":
    continuous_chat()