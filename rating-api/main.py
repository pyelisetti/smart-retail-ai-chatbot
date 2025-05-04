from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import csv
import os
from typing import Dict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Product Rating API",
    description="API for serving product ratings from memory",
    version="1.0.0"
)

# Load ratings into memory on startup
ratings: Dict[str, float] = {}

@app.on_event("startup")
async def load_ratings():
    try:
        logger.info("Starting to load ratings from CSV file...")
        ratings_count = 0
        with open("product_ratings.csv", "r") as file:
            reader = csv.DictReader(file)
            # Log the CSV headers
            logger.info(f"CSV Headers: {reader.fieldnames}")
            
            for row in reader:
                vendor_number = row["Vendor Product Number"]
                rating_value = float(row["Rating"])
                ratings[vendor_number] = rating_value
                ratings_count += 1
                
                # Log the first few entries to verify data format
                if ratings_count <= 5:
                    logger.info(f"Loaded rating - Vendor: {vendor_number}, Rating: {rating_value}")
                
                if ratings_count % 50 == 0:
                    logger.info(f"Loaded {ratings_count} ratings so far...")
        
        logger.info(f"Successfully completed loading ratings. Total ratings loaded: {len(ratings)}")
        logger.info(f"Sample of loaded ratings (first 5): {dict(list(ratings.items())[:5])}")
        
        # Verify specific vendor numbers that were reported missing
        test_vendors = [
            "99e257eb-d66d-4f94-9a03-78ee7e899df9",
            "6a6f3d03-2fba-4f42-af8d-5230f5d48c77",
            "1bb9adb9-f5fc-46b2-9395-98379077d3e2",
            "d6f7bf1c-f78f-47d4-97bf-8c6cf3cecb27",
            "698dfc75-1b8d-4cd7-8994-d8fb1d36ade1"
        ]
        for vendor in test_vendors:
            if vendor in ratings:
                logger.info(f"Verified vendor {vendor} exists with rating {ratings[vendor]}")
            else:
                logger.warning(f"Vendor {vendor} not found in loaded ratings")
                
    except Exception as e:
        logger.error(f"Error loading ratings: {str(e)}")
        raise

class RatingResponse(BaseModel):
    vendor_product_number: str
    rating: float

@app.get("/rating/{vendor_product_number}", response_model=RatingResponse)
async def get_rating(vendor_product_number: str):
    logger.info(f"Looking up rating for product: {vendor_product_number}")
    
    if vendor_product_number not in ratings:
        logger.warning(f"Rating not found for product: {vendor_product_number}, returning default rating of 3")
        return RatingResponse(
            vendor_product_number=vendor_product_number,
            rating=3.0
        )
    
    rating = ratings[vendor_product_number]
    logger.info(f"Found rating {rating} for product: {vendor_product_number}")
    return RatingResponse(
        vendor_product_number=vendor_product_number,
        rating=rating
    )

@app.get("/ratings/count")
async def get_ratings_count():
    return {"count": len(ratings)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8003"))
    uvicorn.run(app, host="0.0.0.0", port=port) 