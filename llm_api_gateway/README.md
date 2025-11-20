# LLM API Gateway

This project provides a unified API to access different Large Language Models (LLMs) like ChatGPT, Gemini, and Grok.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd llm_api_gateway
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Set up your API keys:**
    -   Rename the `.env.example` file to `.env`.
    -   Open the `.env` file and add your API keys for OpenAI and Google.

## Running the Application

1.  **Start the Flask server:**
    ```bash
    python app.py
    ```

2.  **Send a request to the API:**
    You can use a tool like `curl` to send a POST request to the `/api/generate` endpoint.

    **Example for ChatGPT:**
    ```bash
    curl -X POST -H "Content-Type: application/json" -d '{"model": "chatgpt", "prompt": "Hello, world!"}' http://127.0.0.1:5000/api/generate
    ```

    **Example for Gemini:**
    ```bash
    curl -X POST -H "Content-Type: application/json" -d '{"model": "gemini", "prompt": "Tell me a joke."}' http://127.0.0.1:5000/api/generate
    ```
