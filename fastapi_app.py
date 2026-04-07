from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import asyncio

app = FastAPI(
    title="FastAPI Demo 🚀",
    version="1.0.0",
    description="""
## What this demo shows
- ⚡ **Async endpoints** — non-blocking I/O under concurrent load
- ✅ **Pydantic validation** — automatic, typed, with clear error messages
- 📄 **Auto-generated docs** — this page, zero extra work
- 📦 **Typed responses** — `response_model` enforces output shape
""",
)


# ─── Models ───────────────────────────────────────────────────────────────────

class Address(BaseModel):
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    zip_code: str = Field(..., pattern=r"^\d{5}$", description="5-digit US ZIP code")


class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Product name")
    price: float = Field(..., ge=0, description="Unit price in USD")
    quantity: int = Field(..., ge=1, description="Number of units (min 1)")
    tags: list[str] = Field(default=[], description="Optional product tags")
    discount: Optional[float] = Field(None, ge=0, le=1, description="Discount rate (0.0–1.0)")
    ship_to: Optional[Address] = Field(None, description="Optional nested shipping address")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v):
        if not v.strip():
            raise ValueError("name cannot be blank")
        return v.strip()


class OrderResponse(BaseModel):
    message: str
    item: Item
    total: float
    discounted_total: Optional[float] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/fast", summary="Instant response", tags=["Benchmarks"])
async def fast():
    return {"message": "FastAPI response ⚡"}


@app.get("/slow", summary="Simulates I/O wait (non-blocking)", tags=["Benchmarks"])
async def slow():
    await asyncio.sleep(1)  # ✅ yields control — other requests run during this wait
    return {"message": "FastAPI slow endpoint 🐢 (non-blocking)"}


@app.get("/concurrent-demo", summary="Used for concurrency load test", tags=["Benchmarks"])
async def concurrent_demo():
    await asyncio.sleep(1)
    return {"message": "done"}


@app.post(
    "/items",
    response_model=OrderResponse,
    summary="Create an order",
    tags=["Validation"],
)
def create_item(item: Item):
    """
    Demonstrates automatic Pydantic validation. Try sending:
    - A missing field
    - A negative price
    - An invalid ZIP code
    - A discount > 1

    FastAPI returns a structured 422 with per-field errors — no manual try/except needed.
    """
    total = item.price * item.quantity
    discounted = round(total * (1 - item.discount), 2) if item.discount else None
    return OrderResponse(
        message="Validated automatically ✅",
        item=item,
        total=round(total, 2),
        discounted_total=discounted,
    )