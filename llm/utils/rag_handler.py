from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
import os
import logging
from typing import List, Dict, Any
import httpx

logger = logging.getLogger(__name__)

class RAGHandler:
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the RAG handler with an embedding model.
        
        Args:
            embedding_model (str): The name of the sentence transformer model to use
        """
        self.embedding_model = embedding_model
        self.encoder = None
        self.index = None
        self.product_data = []
        self.initialize_embeddings()

    def initialize_embeddings(self):
        """Initialize the embedding model and FAISS index."""
        try:
            logger.info(f"Loading embedding model: {self.embedding_model}")
            self.encoder = SentenceTransformer(self.embedding_model)
            
            # Initialize FAISS index
            dimension = self.encoder.get_sentence_embedding_dimension()
            self.index = faiss.IndexFlatL2(dimension)
            logger.info(f"Initialized FAISS index with dimension {dimension}")
            
            # Load or create product embeddings
            self.load_or_create_embeddings()
        except Exception as e:
            logger.error(f"Error initializing embeddings: {str(e)}")
            raise

    def load_or_create_embeddings(self):
        """Load existing embeddings or create new ones from product data."""
        try:
            # Check for existing embeddings
            embeddings_file = "product_embeddings.npy"
            metadata_file = "product_metadata.json"
            
            if os.path.exists(embeddings_file) and os.path.exists(metadata_file):
                logger.info("Loading existing embeddings and metadata")
                self.index = faiss.read_index(embeddings_file)
                with open(metadata_file, 'r') as f:
                    self.product_data = json.load(f)
            else:
                logger.info("No existing embeddings found, creating new ones")
                self.fetch_and_index_products()
        except Exception as e:
            logger.error(f"Error loading/creating embeddings: {str(e)}")
            raise

    def fetch_and_index_products(self):
        """Fetch products from the MCP server and create embeddings."""
        try:
            mcp_server_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:8001")
            products = []
            
            try:
                with httpx.Client(timeout=10.0) as client:
                    # Fetch all products
                    response = client.post(
                        f"{mcp_server_url}/mcp",
                        json={"method": "get_all_products", "params": {}}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        products = data.get("result", {}).get("products", [])
                        logger.info(f"Successfully fetched {len(products)} products from MCP server")
                    else:
                        logger.warning(f"Failed to fetch products from MCP server: {response.status_code}")
            except Exception as e:
                logger.warning(f"Error connecting to MCP server: {str(e)}")
            
            # If no products were fetched, use fallback data
            if not products:
                logger.info("Using fallback product data")
                products = [
                    {
                        "product_type": "Running Shoes",
                        "brand": "Nike",
                        "color": "Black",
                        "gender": "Men",
                        "age_group": "Adult"
                    },
                    {
                        "product_type": "Sneakers",
                        "brand": "Adidas",
                        "color": "White",
                        "gender": "Women",
                        "age_group": "Adult"
                    },
                    {
                        "product_type": "Sandals",
                        "brand": "Crocs",
                        "color": "Blue",
                        "gender": "Unisex",
                        "age_group": "Adult"
                    }
                ]
            
            if products:
                # Create product descriptions for embedding
                product_descriptions = []
                for product in products:
                    description = self._create_product_description(product)
                    product_descriptions.append(description)
                    self.product_data.append(product)
                
                # Generate embeddings
                embeddings = self.encoder.encode(product_descriptions)
                
                # Add to FAISS index
                self.index.add(np.array(embeddings).astype('float32'))
                
                # Save embeddings and metadata
                faiss.write_index(self.index, "product_embeddings.npy")
                with open("product_metadata.json", 'w') as f:
                    json.dump(self.product_data, f)
                
                logger.info(f"Indexed {len(products)} products")
            else:
                logger.warning("No products found to index")
        except Exception as e:
            logger.error(f"Error fetching and indexing products: {str(e)}")
            raise

    def _create_product_description(self, product: Dict[str, Any]) -> str:
        """Create a text description of a product for embedding."""
        return f"{product.get('product_type', '')} {product.get('brand', '')} {product.get('color', '')} {product.get('gender', '')} {product.get('age_group', '')}"

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant products using the query.
        
        Args:
            query (str): The search query
            k (int): Number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of relevant products
        """
        try:
            # Generate query embedding
            query_embedding = self.encoder.encode([query])
            
            # Search in FAISS index
            distances, indices = self.index.search(
                np.array(query_embedding).astype('float32'), 
                k
            )
            
            # Get relevant products
            results = []
            for idx in indices[0]:
                if idx < len(self.product_data):
                    results.append(self.product_data[idx])
            
            return results
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return []

    def get_relevant_context(self, query: str, k: int = 3) -> str:
        """
        Get relevant product context for a query.
        
        Args:
            query (str): The search query
            k (int): Number of products to include in context
            
        Returns:
            str: Formatted context string
        """
        try:
            relevant_products = self.search(query, k)
            if not relevant_products:
                return "No relevant products found."
            
            context = "Relevant products:\n"
            for i, product in enumerate(relevant_products, 1):
                context += f"{i}. {product.get('product_type', '')} - {product.get('brand', '')} - {product.get('color', '')}\n"
            
            return context
        except Exception as e:
            logger.error(f"Error getting relevant context: {str(e)}")
            return "Error retrieving product context." 