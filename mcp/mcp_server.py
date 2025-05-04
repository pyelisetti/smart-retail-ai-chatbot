from fastapi import FastAPI, HTTPException
from typing import Dict, Any, Optional, List
import requests
from pydantic import BaseModel
import os
import httpx
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MCPRequest(BaseModel):
    method: str
    params: Dict[str, Any]

class MCPResponse(BaseModel):
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

app = FastAPI(
    title="Product MCP Server",
    description="MCP server that uses the Product REST API",
    version="1.0.0"
)

# Get REST API URL from environment variable
REST_API_URL = os.getenv("REST_API_URL", "http://product-api:8000")
RATING_API_URL = os.getenv("RATING_API_URL", "http://rating-api:8003")

async def get_product_rating(vendor_product_number: str) -> Optional[float]:
    """Fetch rating for a product from the rating API."""
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Fetching rating for product: {vendor_product_number}")
            response = await client.get(f"{RATING_API_URL}/rating/{vendor_product_number}")
            if response.status_code == 200:
                rating = response.json().get("rating")
                logger.info(f"Found rating {rating} for product: {vendor_product_number}")
                return rating
            logger.warning(f"No rating found for product: {vendor_product_number}")
            return None
    except Exception as e:
        logger.error(f"Error fetching rating for {vendor_product_number}: {str(e)}")
        return None

async def enrich_products_with_ratings(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enrich products with their ratings from the rating API"""
    enriched_products = []
    for product in products:
        vendor_product_number = product.get("Vendor Product Number")
        if not vendor_product_number:
            logger.warning(f"No Vendor Product Number found for product: {product}")
            enriched_products.append(product)
            continue
            
        try:
            rating = await get_product_rating(vendor_product_number)
            if rating is not None:
                product["rating"] = rating  # Use lowercase 'rating' key
                logger.info(f"Added rating {rating} to product: {vendor_product_number}")
            else:
                logger.warning(f"No rating available for product: {vendor_product_number}")
        except Exception as e:
            logger.error(f"Error enriching product {vendor_product_number} with rating: {str(e)}")
        enriched_products.append(product)
    return enriched_products

@app.post("/mcp", response_model=MCPResponse)
async def process_mcp(request: MCPRequest):
    request_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    logger.info(f"[{request_id}] Received MCP request: {request.dict()}")
    
    try:
        async with httpx.AsyncClient() as client:
            if request.method == "get_products":
                logger.info(f"[{request_id}] Fetching products with params: {request.params}")
                response = await client.get(
                    f"{REST_API_URL}/products",
                    params=request.params
                )
                if response.status_code == 200:
                    products = response.json()
                    logger.info(f"[{request_id}] Fetched {len(products)} products from Product API")
                    # Log first product for debugging
                    if products:
                        logger.info(f"[{request_id}] Sample product data: {products[0]}")
                    # Enrich products with ratings
                    enriched_products = await enrich_products_with_ratings(products)
                    # Log first enriched product for debugging
                    if enriched_products:
                        logger.info(f"[{request_id}] Sample enriched product: {enriched_products[0]}")
                    logger.info(f"[{request_id}] Successfully fetched and enriched {len(enriched_products)} products")
                    return MCPResponse(result={"products": enriched_products})
                else:
                    logger.error(f"[{request_id}] Product API error: {response.status_code} - {response.text}")
                    return MCPResponse(error=f"{response.status_code}: {response.text}")
            elif request.method == "get_product_types":
                logger.info(f"[{request_id}] Fetching product types")
                response = await client.get(f"{REST_API_URL}/product-types")
                if response.status_code == 200:
                    logger.info(f"[{request_id}] Successfully fetched product types")
                    return MCPResponse(result={"product_types": response.json()})
                else:
                    logger.error(f"[{request_id}] Product API error: {response.status_code} - {response.text}")
                    return MCPResponse(error=f"{response.status_code}: {response.text}")
            elif request.method == "get_brands":
                logger.info(f"[{request_id}] Fetching brands")
                response = await client.get(f"{REST_API_URL}/brands")
                if response.status_code == 200:
                    logger.info(f"[{request_id}] Successfully fetched brands")
                    return MCPResponse(result={"brands": response.json()})
                else:
                    logger.error(f"[{request_id}] Product API error: {response.status_code} - {response.text}")
                    return MCPResponse(error=f"{response.status_code}: {response.text}")
            elif request.method == "get_product_subtypes":
                logger.info(f"[{request_id}] Fetching product subtypes")
                response = await client.get(f"{REST_API_URL}/product-subtypes")
                if response.status_code == 200:
                    logger.info(f"[{request_id}] Successfully fetched product subtypes")
                    return MCPResponse(result={"product_subtypes": response.json()})
                else:
                    logger.error(f"[{request_id}] Product API error: {response.status_code} - {response.text}")
                    return MCPResponse(error=f"{response.status_code}: {response.text}")
            elif request.method == "get_colors":
                logger.info(f"[{request_id}] Fetching colors")
                response = await client.get(f"{REST_API_URL}/colors")
                if response.status_code == 200:
                    logger.info(f"[{request_id}] Successfully fetched colors")
                    return MCPResponse(result={"colors": response.json()})
                else:
                    logger.error(f"[{request_id}] Product API error: {response.status_code} - {response.text}")
                    return MCPResponse(error=f"{response.status_code}: {response.text}")
            elif request.method == "get_genders":
                logger.info(f"[{request_id}] Fetching genders")
                response = await client.get(f"{REST_API_URL}/genders")
                if response.status_code == 200:
                    logger.info(f"[{request_id}] Successfully fetched genders")
                    return MCPResponse(result={"genders": response.json()})
                else:
                    logger.error(f"[{request_id}] Product API error: {response.status_code} - {response.text}")
                    return MCPResponse(error=f"{response.status_code}: {response.text}")
            elif request.method == "get_age_groups":
                logger.info(f"[{request_id}] Fetching age groups")
                response = await client.get(f"{REST_API_URL}/age-groups")
                if response.status_code == 200:
                    logger.info(f"[{request_id}] Successfully fetched age groups")
                    return MCPResponse(result={"age_groups": response.json()})
                else:
                    logger.error(f"[{request_id}] Product API error: {response.status_code} - {response.text}")
                    return MCPResponse(error=f"{response.status_code}: {response.text}")
            elif request.method == "clear_context":
                # Clear any stored context or state
                logger.info(f"[{request_id}] Clearing context")
                return MCPResponse(result={"message": "Context cleared successfully"})
            else:
                logger.error(f"[{request_id}] Unknown method requested: {request.method}")
                return MCPResponse(error=f"Unknown method: {request.method}")
    
    except Exception as e:
        logger.error(f"[{request_id}] Error in MCP endpoint: {str(e)}", exc_info=True)
        return MCPResponse(error=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port) 