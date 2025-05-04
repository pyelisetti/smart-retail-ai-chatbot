import streamlit as st
import httpx
import os
from dotenv import load_dotenv
import json
from typing import List, Dict, Any
import time
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure the page
st.set_page_config(
    page_title="Product Search Chat",
    page_icon="🛍️",
    layout="wide"
)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Get API URLs from environment variables
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8002")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001")

def wait_for_service(url: str, max_attempts: int = 12, delay: int = 10) -> bool:
    """Wait for a service to become available"""
    request_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    logger.info(f"[{request_id}] Waiting for service at {url}")
    for attempt in range(max_attempts):
        try:
            with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
                response = client.get(url)
                if response.status_code == 200:
                    logger.info(f"[{request_id}] Service is available")
                    return True
        except Exception as e:
            logger.warning(f"[{request_id}] Attempt {attempt + 1} failed: {str(e)}")
        if attempt < max_attempts - 1:
            time.sleep(delay)
    logger.error(f"[{request_id}] Service is not available after {max_attempts} attempts")
    return False

def clear_context():
    """Clear the context by calling the MCP server"""
    request_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    logger.info(f"[{request_id}] Clearing context")
    try:
        # Wait for MCP server to be ready
        if not wait_for_service(f"{MCP_SERVER_URL}/docs"):
            logger.error(f"[{request_id}] MCP server is not responding")
            st.error("MCP server is not responding. Please try again later.")
            return

        # Create a client with a 10-minute timeout
        timeout = httpx.Timeout(6000.0)  # 3 minutes in seconds
        with httpx.Client(timeout=timeout) as client:
            logger.info(f"[{request_id}] Sending clear context request to MCP server")
            response = client.post(
                f"{MCP_SERVER_URL}/mcp",
                json={"method": "clear_context", "params": {}}
            )
            if response.status_code == 200:
                logger.info(f"[{request_id}] Context cleared successfully")
                st.success("Context cleared successfully")
            else:
                logger.error(f"[{request_id}] Failed to clear context: {response.text}")
                st.error(f"Failed to clear context: {response.text}")
    except httpx.TimeoutException:
        logger.error(f"[{request_id}] Request timed out while clearing context")
        st.error("The request timed out while clearing context. Please try again.")
    except Exception as e:
        logger.error(f"[{request_id}] Error clearing context: {str(e)}", exc_info=True)
        st.error(f"Error clearing context: {str(e)}")

def process_query(query: str) -> str:
    """Process the query through the LLM service"""
    request_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    logger.info(f"[{request_id}] Processing query: {query}")
    
    try:
        # Wait for LLM service to be ready
        if not wait_for_service(f"{LLM_SERVICE_URL}/docs"):
            logger.error(f"[{request_id}] LLM service is not responding")
            return "LLM service is not responding. Please try again later."

        # Create a client with a 5-minute timeout
        timeout = httpx.Timeout(300.0)  # 5 minutes in seconds
        with httpx.Client(timeout=timeout) as client:
            logger.info(f"[{request_id}] Sending query to LLM service")
            response = client.post(
                f"{LLM_SERVICE_URL}/process",
                json={"query": query, "is_structured": False}
            )
            if response.status_code == 200:
                result = response.json()
                if "error" in result and result["error"]:
                    logger.error(f"[{request_id}] LLM service returned error: {result['error']}")
                    return f"Error: {result['error']}"
                logger.info(f"[{request_id}] Successfully processed query")
                return format_response(result.get("result", {}))
            else:
                logger.error(f"[{request_id}] LLM service error: {response.text}")
                return f"Error: {response.text}"
    except httpx.TimeoutException:
        logger.error(f"[{request_id}] Request timed out")
        return "The request timed out. The LLM service is processing your request but it's taking longer than expected. Please try again in a moment."
    except Exception as e:
        logger.error(f"[{request_id}] Error processing query: {str(e)}", exc_info=True)
        return f"Error processing query: {str(e)}"

def format_product(product: Dict[str, Any]) -> str:
    """Format a single product into a natural language description"""
    features = []
    
    if product.get("Product type"):
        features.append(f"a {product['Product type']}")
    if product.get("Brand"):
        features.append(f"from {product['Brand']}")
    if product.get("Color"):
        features.append(f"in {product['Color']}")
    if product.get("Gender"):
        features.append(f"for {product['Gender']}")
    if product.get("Age Group"):
        features.append(f"({product['Age Group']})")
    if product.get("Price"):
        features.append(f"priced at ${product['Price']}")
    
    # Add the rating
    rating = product.get("rating") or product.get("Rating")
    if rating is not None:
        features.append(f"with a rating of {rating}/5")
    
    return " ".join(features)

def generate_nlp_response(products: List[Dict[str, Any]], query: str) -> str:
    """Generate a natural language response based on the products and query"""
    if not products:
        return "I couldn't find any products matching your criteria. Would you like to try a different search?"
    
    # Count products by type
    product_types = {}
    for product in products:
        p_type = product.get("Product type", "Unknown")
        product_types[p_type] = product_types.get(p_type, 0) + 1
    
    # Start building the response
    response_parts = []
    
    # Add a friendly introduction
    if len(products) == 1:
        response_parts.append("I found one product that matches your search:")
    else:
        response_parts.append(f"I found {len(products)} products that match your search:")
    
    # Add product type summary
    if len(product_types) > 1:
        type_summary = ", ".join([f"{count} {ptype}{'s' if count > 1 else ''}" 
                                for ptype, count in product_types.items()])
        response_parts.append(f"Including {type_summary}.")
    
    # Add detailed product descriptions
    response_parts.append("\nHere are the details:")
    
    # Add each product with formatting
    for i, product in enumerate(products, 1):
        product_desc = format_product(product)
        response_parts.append(f"\n{i}. {product_desc}")
    
    # Add a helpful suggestion
    response_parts.append("\nWould you like to know more about any of these products or try a different search?")
    
    return "\n".join(response_parts)

def format_response(response_data: dict) -> str:
    """Format the response data into a natural language string"""
    if not response_data:
        return "I couldn't find any results. Could you please try a different search?"
    
    # If the response is already a string (natural language response), return it directly
    if isinstance(response_data, str):
        return response_data
    
    # If the response contains products, format them
    if "products" in response_data:
        products = response_data["products"]
        return generate_nlp_response(products, "")
    
    # Handle other types of responses
    if isinstance(response_data, dict):
        if "message" in response_data:
            return response_data["message"]
        return json.dumps(response_data, indent=2)
    
    return str(response_data)

def main():
    logger.info(f"[{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}] Streamlit app started")
    # Create the main interface
    st.title("🛍️ Product Search Chat")

    # Add a clear context button
    if st.button("Clear Context"):
        clear_context()

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What products are you looking for?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get assistant response with loading indicator
        with st.chat_message("assistant"):
            with st.spinner("Processing your request... This may take 1-5 minutes as we analyze your query and search through our product database."):
                response = process_query(prompt)
                st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main() 