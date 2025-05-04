from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import logging
from typing import Optional, Dict, Any
import os
from utils.llm_handler import LLMHandler
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMRequest(BaseModel):
    query: str
    is_structured: bool = False

class LLMResponse(BaseModel):
    result: Optional[Dict[str, Any] | str] = None
    error: Optional[str] = None

app = FastAPI(
    title="Product LLM Service",
    description="LLM service for natural language product queries",
    version="1.0.0"
)

# Initialize LLM handler
llm_handler = LLMHandler()

# Get MCP server URL from environment variable
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp-server:8001")

@app.get("/docs")
async def get_docs():
    """Health check endpoint"""
    return {"status": "ok"}

@app.post("/process", response_model=LLMResponse)
async def process_query(request: LLMRequest):
    """
    Process a query through the LLM service.
    
    Args:
        request: The LLM request containing the query and whether it's structured
        
    Returns:
        LLMResponse: The response from the LLM service
    """
    request_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    try:
        # Log the request
        logger.info(f"[{request_id}] Received LLM request: {request.model_dump()}")
        
        if not request.is_structured:
            # Extract structured parameters from natural language
            logger.info(f"[{request_id}] Extracting structured parameters from query: {request.query}")
            structured_params = llm_handler.extract_structured_query(request.query)
            
            # Remove None values and empty strings from params
            structured_params = {k: v for k, v in structured_params.items() if v is not None and v != ""}
            
            logger.info(f"[{request_id}] Extracted structured parameters: {structured_params}")
            
            # Forward to MCP server with increased timeout
            logger.info(f"[{request_id}] Forwarding request to MCP server: {structured_params}")
            async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
                mcp_response = await client.post(
                    f"{MCP_SERVER_URL}/mcp",
                    json={
                        "method": "get_products",
                        "params": structured_params
                    }
                )
                
                if mcp_response.status_code == 200:
                    logger.info(f"[{request_id}] Received successful response from MCP server")
                    mcp_data = mcp_response.json()
                    
                    if not mcp_data.get("result"):
                        return LLMResponse(result="I couldn't find any products matching your search. Could you please try a different search?")
                    
                    # Return the products directly
                    return LLMResponse(result=mcp_data["result"])
                else:
                    logger.error(f"[{request_id}] MCP server error: {mcp_response.status_code} - {mcp_response.text}")
                    return LLMResponse(error=f"MCP server error: {mcp_response.text}")
        else:
            # Process the query directly with Mistral
            logger.info(f"[{request_id}] Processing query directly with Mistral: {request.query}")
            response = llm_handler.process_query(request.query)
            logger.info(f"[{request_id}] Received response from Mistral")
            return LLMResponse(result=response)
            
    except Exception as e:
        logger.error(f"[{request_id}] Error processing query: {str(e)}", exc_info=True)
        return LLMResponse(error=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8002"))
    uvicorn.run(app, host="0.0.0.0", port=port) 