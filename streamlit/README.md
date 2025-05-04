# Product Search Chat Interface

A Streamlit-based chat interface for the Product Search Service.

## Features

- Real-time chat interface for product search
- Clear context functionality
- Formatted product results display
- Persistent chat history within session

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with the following content:
```
LLM_SERVICE_URL=http://localhost:8002
MCP_SERVER_URL=http://localhost:8001
```

3. Make sure the Product Search Service is running (Product API, MCP Server, and LLM Service)

4. Run the Streamlit app:
```bash
streamlit run app.py
```

## Usage

1. Open the app in your browser (default: http://localhost:8501)
2. Type your product search query in the chat input
3. View the formatted results
4. Use the "Clear Context" button to reset the conversation context

## Example Queries

- "Show me all Nike shoes"
- "Find red t-shirts for men"
- "What blue jeans do you have for women?"
- "Show me all products from Adidas" 