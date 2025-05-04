from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import logging
import json
import os
import httpx
from huggingface_hub import login
import time
from .rag_handler import RAGHandler
from typing import Dict, Any, List
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Hardcoded Hugging Face API token
HUGGINGFACE_TOKEN = "REPLACEME"

class LLMHandler:
    def __init__(self):
        try:
            # Initialize GPT-2 model and tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained("gpt2")
            self.model = AutoModelForCausalLM.from_pretrained("gpt2")
            logger.info("LLM Handler initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing LLM Handler: {str(e)}")
            raise

    def process_query(self, query: str, max_length: int = 256) -> str:
        """
        Process a natural language query using the model.
        
        Args:
            query (str): The natural language query
            max_length (int): Maximum length of the generated response
            
        Returns:
            str: The processed response
        """
        try:
            # Extract structured parameters
            structured_params = self.extract_structured_query(query)
            
            # Remove None values and empty strings
            structured_params = {k: v for k, v in structured_params.items() if v is not None and v != ""}
            
            # Forward to MCP server
            mcp_server_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:8001")
            with httpx.Client() as client:
                response = client.post(
                    f"{mcp_server_url}/mcp",
                    json={"method": "get_products", "params": structured_params}
                )
                
                if response.status_code != 200:
                    return "Sorry, I couldn't fetch the products at this time."
                
                result = response.json()
                if not result or "result" not in result:
                    return "I couldn't find any products matching your criteria."
                
                products = result.get("result", {}).get("products", [])
                
                if not products:
                    return "I couldn't find any products matching your criteria."
                
                # Log the first product to check its structure
                if products:
                    logger.info(f"Sample product data in LLM handler: {products[0]}")
                
                return self.generate_nlp_response(products, query)
                
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return "Sorry, I encountered an error while processing your query."

    def extract_structured_query(self, natural_query: str) -> dict:
        """
        Extract structured query parameters from natural language.
        
        Args:
            natural_query (str): The natural language query
            
        Returns:
            dict: Structured query parameters
        """
        try:
            # Initialize default parameters
            structured_params = {
                "product_type": None,
                "gender": None,
                "age_group": None,
                "brand": None,
                "color": None,
                "max_price": None
            }
            
            # Convert query to lowercase for case-insensitive matching
            query_lower = natural_query.lower()
            
            # Extract price constraints
            if "under" in query_lower and "$" in query_lower:
                # Find the price value after "under" and "$"
                price_start = query_lower.find("$") + 1
                price_end = query_lower.find(" ", price_start)
                if price_end == -1:
                    price_end = len(query_lower)
                try:
                    price = float(query_lower[price_start:price_end])
                    structured_params["max_price"] = price
                except ValueError:
                    logger.warning(f"Could not parse price from query: {query_lower}")
            
            # Product type mappings
            product_type_mappings = {
                "shoe": "footwear",
                "shoes": "footwear",
                "sneaker": "footwear",
                "sneakers": "footwear",
                "boot": "footwear",
                "boots": "footwear",
                "sandal": "footwear",
                "sandals": "footwear"
            }
            
            # Extract product type
            for term, mapped_type in product_type_mappings.items():
                if term in query_lower:
                    structured_params["product_type"] = mapped_type
                    break
            
            # Extract brand
            if "adidas" in query_lower:
                structured_params["brand"] = "Adidas"
            elif "nike" in query_lower:
                structured_params["brand"] = "Nike"
            elif "apple" in query_lower:
                structured_params["brand"] = "Apple"
            elif "michael kors" in query_lower:
                structured_params["brand"] = "Michael Kors"
            elif "fossil" in query_lower:
                structured_params["brand"] = "Fossil"
            elif "gucci" in query_lower:
                structured_params["brand"] = "Gucci"
            elif "samsung" in query_lower:
                structured_params["brand"] = "Samsung"
            elif "sony" in query_lower:
                structured_params["brand"] = "Sony"
            elif "amazon" in query_lower:
                structured_params["brand"] = "Amazon"
            elif "coach" in query_lower:
                structured_params["brand"] = "Coach"
            
            # Extract color
            if "red" in query_lower:
                structured_params["color"] = "Red"
            elif "blue" in query_lower:
                structured_params["color"] = "Blue"
            elif "grey" in query_lower or "gray" in query_lower:
                structured_params["color"] = "Grey"
            elif "brown" in query_lower:
                structured_params["color"] = "Brown"
            elif "multi" in query_lower:
                structured_params["color"] = "Multi-color"
            elif "black" in query_lower:
                structured_params["color"] = "Black"
            elif "white" in query_lower:
                structured_params["color"] = "White"
            elif "green" in query_lower:
                structured_params["color"] = "Green"
            elif "yellow" in query_lower:
                structured_params["color"] = "Yellow"
            elif "orange" in query_lower:
                structured_params["color"] = "Orange"
            elif "purple" in query_lower:
                structured_params["color"] = "Purple"
            elif "pink" in query_lower:
                structured_params["color"] = "Pink"
            
            # Extract gender
            if "men" in query_lower or "male" in query_lower:
                structured_params["gender"] = "Male"
            elif "women" in query_lower or "female" in query_lower:
                structured_params["gender"] = "Female"
            elif "kids" in query_lower or "children" in query_lower:
                structured_params["gender"] = "Kids"
            elif "unisex" in query_lower:
                structured_params["gender"] = "Unisex"
            
            # Extract age group
            if "adult" in query_lower:
                structured_params["age_group"] = "Adult"
            elif "youth" in query_lower:
                structured_params["age_group"] = "Youth"
            
            logger.info(f"Extracted structured params: {structured_params}")
            return structured_params
                
        except Exception as e:
            logger.error(f"Error extracting structured query: {str(e)}")
            raise

    def _generate_examples(self) -> str:
        """Generate examples based on available values."""
        examples = []
        
        # Example 1: Basic shoe search
        if self.available_brands and self.available_colors:
            brand = self.available_brands[0]
            color = self.available_colors[0]
            examples.append(f"""
            1. For "Show me {color.lower()} {brand} shoes":
            {{
                "product_type": "shoes",
                "gender": null,
                "age_group": null,
                "brand": "{brand}",
                "color": "{color}"
            }}""")
        
        # Example 2: Age-specific search
        if self.available_brands and self.available_colors and self.available_age_groups:
            brand = self.available_brands[1] if len(self.available_brands) > 1 else self.available_brands[0]
            color = self.available_colors[1] if len(self.available_colors) > 1 else self.available_colors[0]
            age_group = self.available_age_groups[0]
            examples.append(f"""
            2. For "Find {color.lower()} {brand} sneakers for {age_group.lower()}":
            {{
                "product_type": "shoes",
                "gender": null,
                "age_group": "{age_group}",
                "brand": "{brand}",
                "color": "{color}"
            }}""")
        
        # Example 3: Gender-specific search
        if self.available_brands and self.available_colors and self.available_genders:
            brand = self.available_brands[2] if len(self.available_brands) > 2 else self.available_brands[0]
            color = self.available_colors[2] if len(self.available_colors) > 2 else self.available_colors[0]
            gender = self.available_genders[0]
            examples.append(f"""
            3. For "I want {color.lower()} {brand} shoes for {gender.lower()}":
            {{
                "product_type": "shoes",
                "gender": "{gender}",
                "age_group": null,
                "brand": "{brand}",
                "color": "{color}"
            }}""")
        
        # Example 4: Product type search
        if self.available_product_types and self.available_brands and self.available_colors:
            product_type = self.available_product_types[0]
            brand = self.available_brands[3] if len(self.available_brands) > 3 else self.available_brands[0]
            color = self.available_colors[3] if len(self.available_colors) > 3 else self.available_colors[0]
            examples.append(f"""
            4. For "Show me {color.lower()} {brand} {product_type.lower()}":
            {{
                "product_type": "{product_type}",
                "gender": null,
                "age_group": null,
                "brand": "{brand}",
                "color": "{color}"
            }}""")
        
        return "\n".join(examples)

    def generate_response(self, prompt: str) -> str:
        """
        Generate a natural language response using the LLM.
        
        Args:
            prompt: The prompt to generate a response for
            
        Returns:
            str: The generated response
        """
        try:
            # Tokenize the prompt
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
            
            # Generate response
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Decode and clean up the response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove the prompt from the response
            response = response.replace(prompt, "").strip()
            
            # Clean up any remaining special tokens or artifacts
            response = response.replace("<s>", "").replace("</s>", "").strip()
            
            logger.info(f"Generated response: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return "I apologize, but I encountered an error while processing your request. Please try again."

    def _fetch_available_values(self):
        """Fetch all available values from the product API."""
        try:
            import httpx
            mcp_server_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:8001")
            with httpx.Client() as client:
                # Fetch brands
                response = client.post(
                    f"{mcp_server_url}/mcp",
                    json={"method": "get_brands", "params": {}}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("result", {}).get("brands"):
                        self.available_brands = data["result"]["brands"]
                        logger.info(f"Fetched {len(self.available_brands)} available brands")
                
                # Fetch product types
                response = client.post(
                    f"{mcp_server_url}/mcp",
                    json={"method": "get_product_types", "params": {}}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("result", {}).get("product_types"):
                        self.available_product_types = data["result"]["product_types"]
                        logger.info(f"Fetched {len(self.available_product_types)} available product types")
                
                # Fetch genders
                response = client.post(
                    f"{mcp_server_url}/mcp",
                    json={"method": "get_genders", "params": {}}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("result", {}).get("genders"):
                        self.available_genders = data["result"]["genders"]
                        logger.info(f"Fetched {len(self.available_genders)} available genders")
                
                # Fetch age groups
                response = client.post(
                    f"{mcp_server_url}/mcp",
                    json={"method": "get_age_groups", "params": {}}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("result", {}).get("age_groups"):
                        self.available_age_groups = data["result"]["age_groups"]
                        logger.info(f"Fetched {len(self.available_age_groups)} available age groups")
                
                # Fetch colors
                response = client.post(
                    f"{mcp_server_url}/mcp",
                    json={"method": "get_colors", "params": {}}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("result", {}).get("colors"):
                        self.available_colors = data["result"]["colors"]
                        logger.info(f"Fetched {len(self.available_colors)} available colors")
                
        except Exception as e:
            logger.error(f"Error fetching available values: {str(e)}")
            self.available_brands = None
            self.available_product_types = None
            self.available_genders = None
            self.available_age_groups = None
            self.available_colors = None 

    def format_product(self, product: Dict[str, Any]) -> str:
        """Format a single product into a natural language description"""
        features = []
        
        # Log the product data before formatting
        logger.info(f"Formatting product: {product}")
        
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
        
        # Check for rating in both lowercase and uppercase
        rating = product.get("rating") or product.get("Rating") # Hard coding rating to 3.0
        if rating is not None:
            features.append(f"with a rating of {rating}/5")
            logger.info(f"Added rating {rating} to product description")
        else:
            logger.warning(f"No rating found for product: {product.get('Vendor Product Number')}")
        
        formatted_desc = " ".join(features)
        logger.info(f"Formatted product description: {formatted_desc}")
        return formatted_desc

    def generate_nlp_response(self, products: List[Dict[str, Any]], query: str) -> str:
        """Generate a natural language response based on the products and query"""
        if not products:
            return "I couldn't find any products matching your criteria. Would you like to try a different search?"
        
        # Log the products received
        logger.info(f"Generating response for {len(products)} products")
        logger.info(f"Sample product data: {products[0]}")
        
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
            logger.info(f"Formatting product {i}: {product}")
            product_desc = self.format_product(product)
            logger.info(f"Formatted description {i}: {product_desc}")
            response_parts.append(f"\n{i}. {product_desc}")
        
        # Add a helpful suggestion
        response_parts.append("\nWould you like to know more about any of these products or try a different search?")
        
        final_response = "\n".join(response_parts)
        logger.info(f"Generated final response: {final_response}")
        return final_response 