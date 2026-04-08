from fastapi import FastAPI, HTTPException, Query, Path
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
import uvicorn

# FastAPI app initialization - Simple and clean!
app = FastAPI(
    title="FastAPI Demo API",
    description="This demonstrates FastAPI's speed, validation, and automatic docs",
    version="1.0.0"
)

# Pydantic models for automatic validation
class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Item name")
    price: float = Field(..., gt=0, description="Price must be greater than 0")
    quantity: int = Field(..., ge=1, le=1000, description="Quantity between 1-1000")
    tags: Optional[List[str]] = Field(default=[], max_items=10)
    
    # Custom validation - automatic and type-safe!
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty or just whitespace')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Gaming Laptop",
                "price": 999.99,
                "quantity": 5,
                "tags": ["electronics", "gaming"]
            }
        }

class ItemResponse(Item):
    id: int
    created_at: datetime
    total_value: float

# In-memory storage
items_db = {}
item_counter = 1

@app.get("/", tags=["Root"])
async def root():
    """Simple root endpoint - Notice how clean this is!"""
    return {
        "message": "Welcome to FastAPI Demo!",
        "docs": "Visit /docs for automatic interactive documentation",
        "redoc": "Visit /redoc for alternative documentation"
    }

@app.post("/items/", response_model=ItemResponse, status_code=201, tags=["Items"])
async def create_item(item: Item):
    """
    Create a new item - FastAPI automatically:
    - Validates all input data
    - Generates JSON Schema
    - Provides type hints and autocomplete
    """
    global item_counter
    
    # No manual validation needed - FastAPI already validated everything!
    new_item = {
        "id": item_counter,
        **item.dict(),
        "created_at": datetime.now(),
        "total_value": item.price * item.quantity
    }
    
    items_db[item_counter] = new_item
    item_counter += 1
    
    return new_item

@app.get("/items/", response_model=List[ItemResponse], tags=["Items"])
async def list_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max items to return"),
    min_price: Optional[float] = Query(None, gt=0, description="Filter by minimum price")
):
    """
    List all items with pagination and filtering.
    FastAPI handles query parameter validation automatically!
    """
    items = list(items_db.values())
    
    # Apply filters
    if min_price is not None:
        items = [item for item in items if item["price"] >= min_price]
    
    # Apply pagination
    return items[skip:skip + limit]

@app.get("/items/{item_id}", response_model=ItemResponse, tags=["Items"])
async def get_item(
    item_id: int = Path(..., gt=0, description="The ID of the item to retrieve")
):
    """
    Get a specific item by ID.
    FastAPI validates the path parameter automatically!
    """
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    
    return items_db[item_id]

@app.put("/items/{item_id}", response_model=ItemResponse, tags=["Items"])
async def update_item(
    item_id: int = Path(..., gt=0),
    item: Item = None  # FastAPI validates this automatically
):
    """Update an existing item with automatic validation"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    
    updated_item = {
        "id": item_id,
        **item.dict(),
        "created_at": items_db[item_id]["created_at"],
        "total_value": item.price * item.quantity
    }
    
    items_db[item_id] = updated_item
    return updated_item

@app.delete("/items/{item_id}", tags=["Items"])
async def delete_item(item_id: int = Path(..., gt=0)):
    """Delete an item"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    
    del items_db[item_id]
    return {"message": f"Item {item_id} successfully deleted"}

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "items_count": len(items_db),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Run with: python fastapi_app.py
    uvicorn.run(
        "fastapi_app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Auto-reload during development
        log_level="info"
    )