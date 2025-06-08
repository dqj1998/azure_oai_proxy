# Azure OpenAI Proxy (FastAPI)

This Python project implements a proxy server that forwards JSON requests to the Azure OpenAI API, handling Azure AD authentication and providing an interactive API documentation UI via Swagger.

## Table of Contents

- [Azure OpenAI Proxy (FastAPI)](#azure-openai-proxy-fastapi)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Usage](#usage)
  - [API Documentation](#api-documentation)
  - [Environment Variables](#environment-variables)
  - [Endpoints](#endpoints)
  - [Client setting](#client-setting)
  - [License](#license)

## Prerequisites

- Python 3.8 or newer
- An Azure subscription with an OpenAI resource deployed
- Valid Azure AD credentials with permissions to access the OpenAI resource

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/azure_oai_proxy.git
   cd azure_oai_proxy
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the Python dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Configuration

1. Copy the example environment file and set your credentials:
   ```bash
   cp .env-example .env
   ```
2. Edit `.env` and populate the following variables:
   ```
   AZURE_OPENAI_ENDPOINT=https://<your-azure-openai-endpoint>.openai.azure.com/
   AZURE_TENANT_ID=<your-azure-tenant-id>
   AZURE_CLIENT_ID=<your-azure-client-id>
   AZURE_CLIENT_SECRET=<your-azure-client-secret>
   PORT=8899
   ```

## Usage

Start the FastAPI server with Uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8899} --reload
```

The proxy will listen on `http://localhost:8899` by default.

## API Documentation

Open your browser and navigate to:

- Swagger UI: `http://localhost:8899/docs`
- ReDoc: `http://localhost:8899/redoc`

## Environment Variables

- `AZURE_TENANT_ID`: Azure AD tenant ID.
- `AZURE_CLIENT_ID`: Service principal client ID.
- `AZURE_CLIENT_SECRET`: Service principal client secret.
- `AZURE_OPENAI_ENDPOINT`: Base URL of your Azure OpenAI resource.
- `PORT`: (Optional) HTTP port for Uvicorn, default is `8899`.

## Endpoints

- `GET /check`: A simple endpoint to check if the proxy is working.
  - **Request**: None.
  - **Response**: JSON object with status and response message.

- `POST /v1/chat/completions`: Forward a JSON body to the Azure OpenAI chat completion API with optional streaming support.
  - **Request**: JSON body with parameters compliant with the Azure OpenAI specification, including messages, model, temperature, max_tokens, etc.
  - **Response**: JSON response from Azure OpenAI, with streaming support if requested.

## Client setting

- Example of VSCode Cline
  
  ![Az-conf-cliennt-4 1](https://github.com/user-attachments/assets/d3929535-4846-4ded-ae6d-253ec9de3872)


  * The API key can be any text
  
- Open AI URL of VSWizard[https://github.com/dqj1998/VSWizard.git]
  
  http://localhost:8899/v1/chat/completions

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.
