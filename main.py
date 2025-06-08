import os
from dotenv import load_dotenv
from azure_oai_caller import init_ai_caller
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import time
import uuid

load_dotenv()

app = FastAPI(
    title="Azure OpenAI Proxy",
    description="Proxy server forwarding requests to Azure OpenAI with Azure AD authentication",
    version="1.0.0"
)

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: list[Message]
    model: str = "gpt-4o" # Default model
    # Add other parameters as needed, e.g., temperature, max_tokens, etc.
    temperature: float = 0.7
    max_tokens: int = 4000
    top_p: float = 0.95
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: list[str] | None = None
    stream: bool = False # Added for streaming support

class ChatCompletionResponseChoiceMessage(BaseModel):
    role: str
    content: str

class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatCompletionResponseChoiceMessage
    logprobs: None = None
    finish_reason: str = "stop"

class ChatCompletionResponseUsage(BaseModel):
    prompt_tokens: int = 0 # Placeholder, as process_message doesn't return this
    completion_tokens: int = 0 # Placeholder
    total_tokens: int = 0 # Placeholder

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionResponseChoice]
    usage: ChatCompletionResponseUsage

init_ai_caller()

# Enable CORS for testing via docs UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/check")
async def proxy():
    """
    Simple endpoint to check if the proxy is working.
    """
    try:
        # Use the Azure OpenAI client to make a simple request
        from azure_oai_caller import ai_client
        response = ai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a test bot."}],
            temperature=0.7,
            max_tokens=10
        )
        return {"status": "success", "response": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import Request
import json
@app.post("/v1/chat/completions")
async def create_chat_completion(request: Request):
    from azure_oai_caller import process_message
    try:
        body = await request.json() 

        messages_for_process = body['messages']
        
        if request.stream:
            # For streaming responses, process_message yields chunks
            return StreamingResponse(process_message(messages_for_process), media_type="text/event-stream")
        else:
            # For non-streaming responses, we need to collect the full response
            full_ai_response_content = ""
            chat_id = None
            for chunk in process_message(messages_for_process):
                # Extract content from the chunk to build full_ai_response_content
                if chunk.startswith("data:"):
                    line = chunk.replace("data: ", "").strip()
                    if line == "[DONE]":
                        break
                    try:
                        data = json.loads(line)
                        delta = data.get('choices', [{}])[0].get('delta', {}).get('content')
                        if delta:
                            full_ai_response_content += delta
                    except json.JSONDecodeError:
                        pass # Ignore parse errors
                # The last yield from process_message is the chat_id, which we capture here
                if not chunk.startswith("data:"):
                    chat_id = chunk # This is the chat_id returned by process_message

            # Construct the response based on OpenAI API format
            response_id = f"chatcmpl-{uuid.uuid4()}"
            created_time = int(time.time())

            response_message = ChatCompletionResponseChoiceMessage(
                role="assistant",
                content=full_ai_response_content
            )
            response_choice = ChatCompletionResponseChoice(
                index=0,
                message=response_message
            )
            response_usage = ChatCompletionResponseUsage(
                prompt_tokens=0, # Placeholder, as process_message doesn't return this
                completion_tokens=0, # Placeholder
                total_tokens=0 # Placeholder
            )

            return ChatCompletionResponse(
                id=response_id,
                created=created_time,
                model=request.model,
                choices=[response_choice],
                usage=response_usage
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8899))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
