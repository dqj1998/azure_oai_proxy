import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from azure_auth import get_azure_token

load_dotenv()

app = FastAPI(
    title="Azure OpenAI Proxy",
    description="Proxy server forwarding requests to Azure OpenAI with Azure AD authentication",
    version="1.0.0"
)

# Enable CORS for testing via docs UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/proxy")
async def proxy(request_body: dict):
    """
    Forward incoming JSON requests to the Azure OpenAI endpoint.
    """
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    model = os.getenv("AZURE_OPENAI_MODEL")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-03-15-preview")

    if not endpoint or not model:
        raise HTTPException(status_code=500, detail="AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_MODEL not set")

    token = await get_azure_token()
    url = f"{endpoint}/openai/deployments/{model}/chat/completions?api-version={api_version}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=request_body, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8899))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
