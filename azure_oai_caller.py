import json
import os
import uuid
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
from azure.identity import get_bearer_token_provider

global ai_client

# Global map to store chat histories by chat_id
global chat_histories
chat_histories = {}

def generate_chat_id():
    """Generate a unique chat_id."""
    return str(uuid.uuid4())

def init_ai_caller():
    """
    Initialize AI utilities by loading environment variables and setting up the Azure OpenAI client.
    """

    # Read Azure credentials from environment variables
    os.environ['AZURE_CLIENT_ID'] = os.getenv('AZURE_CLIENT_ID')
    os.environ['AZURE_CLIENT_SECRET'] = os.getenv('AZURE_CLIENT_SECRET')
    os.environ['AZURE_TENANT_ID'] = os.getenv('AZURE_TENANT_ID')

    default_credential = DefaultAzureCredential()

    token_provider = get_bearer_token_provider(default_credential, "https://cognitiveservices.azure.com/.default")

    global ai_client
    ai_client = AzureOpenAI(azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
        azure_ad_token_provider=token_provider,
        api_version="2023-12-01-preview")

def generate_response(messages: list, model: str = "gpt-4o", stream: bool = False):
    response = ai_client.chat.completions.create(model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=4000,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
        stream=stream)

    if stream:
        for chunk in response:
            if not chunk.choices or not chunk.choices[0].delta:
                continue
            if not chunk.choices[0].delta.content:
                continue
            # If the delta content is empty, skip to the next chunk
            if chunk.choices[0].finish_reason:
                yield "data: [DONE]\n\n"
                break
            delta = chunk.choices[0].delta.content
            if delta:
                yield f"data: {json.dumps({'choices': [{'delta': {'content': delta}}]})}\n\n"
        yield "data: [DONE]\n\n"
    else:
        return response.choices[0].message.content

def process_message(message: list, chat_id: str = None):
    """
    Process user message and generate AI response.
    Yields:
      - ai response chunks: str
    Returns:
      - conversation history: list (after stream is complete)
    """
    global chat_histories

    if not chat_id:
        chat_id = generate_chat_id()

    if chat_id not in chat_histories:
        chat_histories[chat_id] = []

    # Removed print statement
    new_history = chat_histories[chat_id].copy()

    new_history += message

    # Validate and ensure the messages list is properly formatted
    for msg in new_history:
        if "role" not in msg or "content" not in msg:
            raise ValueError("Each message must include 'role' and 'content' fields.")

    full_ai_response_content = ""
    for chunk in generate_response(new_history, stream=True):
        yield chunk
        # Extract content from the chunk to build full_ai_response_content for history
        if chunk.startswith("data:"):
            line = chunk.replace("data: ", "").strip()
            if line != "[DONE]":
                try:
                    data = json.loads(line)
                    delta = data.get('choices', [{}])[0].get('delta', {}).get('content')
                    if delta:
                        full_ai_response_content += delta
                except json.JSONDecodeError:
                    pass # Ignore parse errors

    # Removed print statement

    # Append AI response to history
    new_history.append({"role": "assistant", "content": full_ai_response_content})
    chat_histories[chat_id] = new_history

    return chat_id # Return chat_id after the stream is complete
