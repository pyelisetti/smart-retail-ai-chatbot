from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
import pandas as pd
import os
import math
import numpy as np
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj) or np.isnan(obj) or np.isinf(obj):
                return None
        return super().default(obj)

app = FastAPI(
    title="Product API",
    description="REST API for product data",
    version="1.0.0"
)

# Load product data
df = pd.read_csv('products.csv')
logger.info(f"Loaded {len(df)} products")

@app.get("/products")
async def get_products(
    product_type: Optional[str] = Query(None, description="Filter by product type"),
    product_subtype: Optional[str] = Query(None, description="Filter by product subtype"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    age_group: Optional[str] = Query(None, description="Filter by age group"),
    color: Optional[str] = Query(None, description="Filter by color"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price")
):
    logger.info(f"[{datetime.now().isoformat()}] Received products request - product_type: {product_type}, brand: {brand}, product_subtype: {product_subtype}, color: {color}, gender: {gender}, age_group: {age_group}")
    try:
        filtered_df = df.copy()
        logger.info(f"Starting with {len(filtered_df)} products")

        # Filter by basic fields with case-insensitive partial matching
        if product_type:
            try:
                filtered_df = filtered_df[filtered_df['Product type'].str.lower().str.contains(product_type.lower(), na=False)]
                logger.info(f"After product_type filter: {len(filtered_df)} products")
            except:
                logger.warning("Error filtering by product_type, continuing without filter")
        if product_subtype:
            try:
                filtered_df = filtered_df[filtered_df['Product subtype'].str.lower().str.contains(product_subtype.lower(), na=False)]
                logger.info(f"After product_subtype filter: {len(filtered_df)} products")
            except:
                logger.warning("Error filtering by product_subtype, continuing without filter")
        if gender:
            try:
                filtered_df = filtered_df[filtered_df['Gender'].str.lower().str.contains(gender.lower(), na=False)]
                logger.info(f"After gender filter: {len(filtered_df)} products")
            except:
                logger.warning("Error filtering by gender, continuing without filter")
        if age_group:
            try:
                filtered_df = filtered_df[filtered_df['Age Group'].str.lower().str.contains(age_group.lower(), na=False)]
                logger.info(f"After age_group filter: {len(filtered_df)} products")
            except:
                logger.warning("Error filtering by age_group, continuing without filter")
        if color:
            try:
                filtered_df = filtered_df[filtered_df['Color'].str.lower().str.contains(color.lower(), na=False)]
                logger.info(f"After color filter: {len(filtered_df)} products")
            except:
                logger.warning("Error filtering by color, continuing without filter")
        if brand:
            try:
                filtered_df = filtered_df[filtered_df['Brand'].str.lower().str.contains(brand.lower(), na=False)]
                logger.info(f"After brand filter: {len(filtered_df)} products")
            except:
                logger.warning("Error filtering by brand, continuing without filter")

        if min_price is not None:
            try:
                filtered_df = filtered_df[filtered_df["Price"] >= min_price]
            except:
                logger.warning("Error filtering by min_price, continuing without filter")
        if max_price is not None:
            try:
                filtered_df = filtered_df[filtered_df["Price"] <= max_price]
            except:
                logger.warning("Error filtering by max_price, continuing without filter")

        # Convert to records and clean them
        results = filtered_df.replace([np.inf, -np.inf, np.nan], None).to_dict(orient="records")
        return json.loads(json.dumps(results, cls=CustomJSONEncoder))

    except Exception as e:
        logger.error(f"Error in get_products: {str(e)}")
        return []  # Return empty list if there's any error

@app.get("/product-types")
async def get_product_types():
    logger.info(f"[{datetime.now().isoformat()}] Received product-types request")
    return df['Product type'].dropna().unique().tolist()

@app.get("/brands")
async def get_brands():
    logger.info(f"[{datetime.now().isoformat()}] Received brands request")
    return df['Brand'].dropna().unique().tolist()

@app.get("/product-subtypes")
async def get_product_subtypes():
    logger.info(f"[{datetime.now().isoformat()}] Received product-subtypes request")
    return df['Product subtype'].dropna().unique().tolist()

@app.get("/colors")
async def get_colors():
    logger.info(f"[{datetime.now().isoformat()}] Received colors request")
    return df['Color'].dropna().unique().tolist()

@app.get("/genders")
async def get_genders():
    logger.info(f"[{datetime.now().isoformat()}] Received genders request")
    return df['Gender'].dropna().unique().tolist()

@app.get("/age-groups")
async def get_age_groups():
    logger.info(f"[{datetime.now().isoformat()}] Received age-groups request")
    return df['Age Group'].dropna().unique().tolist()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
