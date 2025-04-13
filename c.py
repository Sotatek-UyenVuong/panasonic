import anthropic
import os
from dotenv import load_dotenv
load_dotenv()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

with client.messages.stream(
    model="claude-3-7-sonnet-20250219",
    max_tokens=20000,
    thinking={
        "type": "enabled",
        "budget_tokens": 16000
    },
    messages=[{
        "role": "user",
        "content": "What is 27 * 453?"
    }]
) as stream:
    for event in stream:
        if event.type == "content_block_start":
            print(f"\nStarting {event.content_block.type} block...")
        elif event.type == "content_block_delta":
            if event.delta.type == "thinking_delta":
                print(f"Thinking: {event.delta.thinking}", end="", flush=True)
            elif event.delta.type == "text_delta":
                print(f"Response: {event.delta.text}", end="", flush=True)
        elif event.type == "content_block_stop":
            print("\nBlock complete.")
