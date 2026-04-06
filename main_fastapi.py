from fastapi import FastAPI
from pydantic import BaseModel
import asyncio

app = FastAPI(title="FastAPI Demo")

class Item(BaseModel):
    name: str
    price: float
    quantity: int


@app.get("/fast")
async def fast():
    return {"message": "FastAPI response ⚡"}


@app.get("/slow")
async def slow():
    await asyncio.sleep(1)
    return {"message": "FastAPI slow endpoint 🐢 (non-blocking)"}


@app.post("/items")
def create_item(item: Item):
    return {
        "message": "Validated automatically",
        "item": item,
        "total": item.price * item.quantity
    }