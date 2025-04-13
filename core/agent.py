import os
from dotenv import load_dotenv
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings
from typing import Optional, Tuple, List
from llama_index.core.tools import FunctionTool, ToolMetadata, QueryEngineTool
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.chat_engine.types import BaseChatEngine
from llama_index.core.base.response.schema import Response
import tiktoken
import asyncio
from llama_index.core.prompts import PromptTemplate
react_system_header_str = """\
You are designed to help with a variety of tasks, from answering questions \
    to providing summaries to other types of analyses.

## Tools
You have access to a wide variety of tools. You are responsible for using
the tools in any sequence you deem appropriate to complete the task at hand.
This may require breaking the task into subtasks and using different tools
to complete each subtask.

You have access to the following tools:
{tool_desc}

## Output Format
Please answer in Vietnamese and use the following format:

```
Thought: I need to use the panasonic_manual tool to find information about this question.
Action: panasonic_manual
Action Input: {{"input": "your detailed question here"}}
```

Please ALWAYS start with a Thought and ALWAYS use the panasonic_manual tool first.

Please use a valid JSON format for the Action Input. Do NOT do this {{'input': 'hello world'}}.

If this format is used, the tool will respond in the following format:

```
Observation: tool response
```

You should keep repeating the above format until you have enough information
to answer the question without using any more tools. At that point, you MUST respond
in one of the following two formats:

```
Thought: I can answer without using any more tools.
Answer: [your answer here in Vietnamese]

IMPORTANT: Each sentence in your answer MUST end with a page citation in the format [Page X] where X is the page number from the source material. For example:
"Nhấn nút F1 để tăng độ sáng màn hình [Page 1]. Menu sẽ xuất hiện ở bên phải [Page 2]."

If you cannot determine the page number for a particular piece of information, use [Page N/A].
If multiple pages contain the same information, you can cite them together like [Page 1, 2].
```

```
Thought: I cannot find the specific information in the Panasonic manual.
Answer: Xin lỗi, tôi không tìm thấy thông tin cụ thể về vấn đề này trong tài liệu hướng dẫn Panasonic.
```

## Additional Rules
- You MUST ALWAYS use the panasonic_manual tool to search for information before providing an answer.
- Every sentence in your answer MUST end with a page citation [Page X].
- If multiple pages contain the same information, you can cite them together like [Page 1, 2].
- If you cannot find the specific information in the Panasonic manual, clearly state that.
- Always respond in Vietnamese with page citations.

## Current Conversation
Below is the current conversation consisting of interleaving human and assistant messages.
"""
react_system_prompt = PromptTemplate(react_system_header_str)

# Configure LLM settings
model = "gpt-4o-mini"
Settings.llm = OpenAI(model=model)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

from llama_index.core import StorageContext, load_index_from_storage

try:
    storage_context = StorageContext.from_defaults(
        persist_dir="./storage/panasonic"
    )
    panasonic_index = load_index_from_storage(storage_context)
    index_loaded = True
except:
    index_loaded = False

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex

if not index_loaded:
    # load data
    panasonic_docs = SimpleDirectoryReader(
        input_files=["/Users/uyenbaby/Downloads/panasonic_reasoning/data/documents.json"]
    ).load_data()
    
    # build index
    panasonic_index = VectorStoreIndex.from_documents(panasonic_docs)
    
    # persist index
    panasonic_index.storage_context.persist(persist_dir="./storage/panasonic")

panasonic_engine = panasonic_index.as_query_engine(
    similarity_top_k=15,
    response_mode="compact",
    verbose=True,
    response_synthesizer_kwargs={
        "include_metadata": True,
        "metadata_keys": ["page_number"]
    }
)

query_engine_tools = [
    QueryEngineTool.from_defaults(
        query_engine=panasonic_engine,
        name="panasonic_manual",
        description=(
            "Provides information about Panasonic manual. "
            "Use a detailed plain text question as input to the tool."
        ),
    )
]

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.agent import ReActAgent
from llama_index.core.agent.workflow import ToolCallResult, AgentStream

# Create a separate LLM instance for analysis
analysis_llm = OpenAI(model="gpt-4o-mini")

class EnhancedReActAgent(ReActAgent):
    """Enhanced ReAct Agent that can ask follow-up questions when needed."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.awaiting_clarification = False
        self.pending_query = None
        self.missing_info = None
        # Store the LLM instance explicitly
        self.analysis_llm = analysis_llm
    
    async def achat(self, message: str) -> Response:
        """Override of achat to handle follow-up questions."""
        
        # If we're awaiting clarification, combine the original query with the new information
        if self.awaiting_clarification and self.pending_query:
            combined_message = f"Original question: {self.pending_query}\nAdditional information: {message}"
            self.awaiting_clarification = False
            self.pending_query = None
            self.missing_info = None
            return await super().achat(combined_message)
        
        # First, analyze if the query has enough information to answer properly
        analysis_prompt = f"""
        Analyze the following user query about Panasonic products and determine if there's sufficient information to provide a complete answer:
        
        "{message}"
        
        If there is missing critical information, please identify:
        1. What specific details are missing (model number, feature name, specific function, etc.)
        2. What clarifying questions should be asked to the user
        
        Output format:
        SUFFICIENT: true/false
        MISSING_INFO: <describe what's missing if applicable>
        QUESTIONS: <1-3 specific questions to ask if applicable>
        """
        
        # Use the separate LLM instance for analysis
        analysis_response = await self.analysis_llm.acomplete(analysis_prompt)
        analysis_text = analysis_response.text
        
        # Parse the analysis to determine if we need more information
        has_sufficient_info = "SUFFICIENT: true" in analysis_text.upper()
        
        if not has_sufficient_info:
            # Extract the missing information and questions
            missing_info_start = analysis_text.upper().find("MISSING_INFO:")
            questions_start = analysis_text.upper().find("QUESTIONS:")
            
            if missing_info_start != -1 and questions_start != -1:
                missing_info = analysis_text[missing_info_start + len("MISSING_INFO:"):questions_start].strip()
                questions = analysis_text[questions_start + len("QUESTIONS:"):].strip()
                
                # Set the flags and store the original query
                self.awaiting_clarification = True
                self.pending_query = message
                self.missing_info = missing_info
                
                # Return the clarifying questions as the response
                return Response(response=f"Để trả lời chính xác hơn, tôi cần thêm một số thông tin:\n\n{questions}")
        
        # If we have sufficient information or couldn't properly parse the analysis, proceed with the normal flow
        return await super().achat(message)

# Initialize chat memory
memory = ChatMemoryBuffer.from_defaults(token_limit=40000)


# Create the enhanced agent
agent = EnhancedReActAgent(
    tools=query_engine_tools,
    llm=OpenAI(model="gpt-4o-mini"),
    memory=memory,
    verbose=True
)


async def chat_stream():
    """
    Chat function that handles streaming responses from the agent using event streaming.
    Includes Vietnamese language interface and proper memory management.
    """
    print("\nXin chào! Tôi là trợ lý ảo về sản phẩm Panasonic. Hãy đặt câu hỏi cho tôi. (Gõ 'thoát' để kết thúc)")
    print("-" * 50)
    
    while True:
        try:
            # Get user input
            user_input = input("\nBạn: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['thoát', 'exit', 'quit']:
                print("\nTạm biệt! Hẹn gặp lại!")
                break
                
            if not user_input:
                print("Vui lòng nhập câu hỏi của bạn.")
                continue
                
            print("\nTrợ lý:", end=" ", flush=True)
            agent.update_prompts({"react_header": react_system_prompt})
            prompt_dict = agent.get_prompts()
            print(prompt_dict)
            
            
            # Process the query and get response
            response = await agent.achat(user_input)
            
            # Print the response
            if response and response.response:
                print(response.response)
            else:
                print("Xin lỗi, tôi không thể xử lý câu hỏi này.")
                
        except asyncio.CancelledError:
            print("\nĐã hủy yêu cầu.")
            continue
            
        except KeyboardInterrupt:
            print("\n\nTạm biệt! Hẹn gặp lại!")
            break
            
        except Exception as e:
            print(f"\nCó lỗi xảy ra: {str(e)}")
            import traceback
            traceback.print_exc()  # In ra stack trace đầy đủ để debug
            continue

if __name__ == "__main__":
    # Run the async chat function
    asyncio.run(chat_stream())
