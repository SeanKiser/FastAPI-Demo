from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import asyncio
import time
import uuid
from datetime import datetime

app = FastAPI(
    title="AI Inference API - FastAPI",
    description="High-performance API for AI workloads with async support",
    version="1.0.0"
)

# Request/Response Models with built-in validation
class EmbeddingRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000, description="Input text to embed")
    model: str = Field("fast-sbert", description="Embedding model to use")

class EmbeddingResponse(BaseModel):
    embedding: List[float]
    dimension: int
    latency_ms: float
    request_id: str

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Input prompt")
    max_tokens: int = Field(100, ge=1, le=500, description="Maximum tokens to generate")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")

class GenerateResponse(BaseModel):
    generated_text: str
    tokens_generated: int
    latency_ms: float
    request_id: str

class BatchEmbeddingRequest(BaseModel):
    texts: List[str] = Field(..., min_items=1, max_items=100, description="Batch of texts")
    model: str = "fast-sbert"

# Simulated AI workloads
async def simulate_embedding(text: str) -> List[float]:
    """Simulate embedding generation with realistic delay"""
    # Simulate compute time proportional to text length
    compute_time = min(0.01 * len(text), 0.1)  # 10ms per 1000 chars max 100ms
    await asyncio.sleep(compute_time)
    # Return mock embedding vector
    return [float(hash(f"{text}_{i}") % 1000) / 1000 for i in range(384)]

async def simulate_generation(prompt: str, max_tokens: int) -> str:
    """Simulate LLM text generation"""
    # Simulate token-by-token generation with realistic delay
    tokens = []
    for i in range(max_tokens):
        await asyncio.sleep(0.01)  # 10ms per token
        tokens.append(f"token_{i}")
    return f"Generated response for: '{prompt[:50]}...' using {len(tokens)} tokens"

# Async endpoints for maximum concurrency
@app.post("/embed", response_model=EmbeddingResponse, status_code=200)
async def generate_embedding(request: EmbeddingRequest):
    """Generate embeddings for input text. Async handler allows concurrent requests."""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        embedding = await simulate_embedding(request.text)
        latency_ms = (time.time() - start_time) * 1000
        
        return EmbeddingResponse(
            embedding=embedding,
            dimension=len(embedding),
            latency_ms=round(latency_ms, 2),
            request_id=request_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")

@app.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """Generate text using simulated LLM. Async handles multiple concurrent requests efficiently."""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        generated = await simulate_generation(request.prompt, request.max_tokens)
        latency_ms = (time.time() - start_time) * 1000
        
        return GenerateResponse(
            generated_text=generated,
            tokens_generated=request.max_tokens,
            latency_ms=round(latency_ms, 2),
            request_id=request_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.post("/embed/batch", response_model=List[EmbeddingResponse])
async def batch_embedding(request: BatchEmbeddingRequest):
    """Process multiple embeddings concurrently - where async really shines!"""
    start_time = time.time()
    tasks = [simulate_embedding(text) for text in request.texts]
    embeddings = await asyncio.gather(*tasks)
    
    responses = []
    for text, embedding in zip(request.texts, embeddings):
        responses.append(EmbeddingResponse(
            embedding=embedding,
            dimension=len(embedding),
            latency_ms=round((time.time() - start_time) * 1000 / len(request.texts), 2),
            request_id=str(uuid.uuid4())
        ))
    return responses

@app.get("/health")
async def health_check():
    """Quick health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/docs")
async def get_docs():
    """FastAPI automatically generates interactive API documentation at /docs"""
    return {
        "message": "Interactive API docs available at /docs",
        "openapi": "/openapi.json"
    }

# Simulated streaming endpoint for true AI workloads
@app.post("/generate/stream")
async def generate_stream(request: GenerateRequest):
    """Stream generated text token by token - impossible in Flask without hacks"""
    async def token_generator():
        for i in range(request.max_tokens):
            await asyncio.sleep(0.01)
            yield f"data: token_{i}\n\n"
        yield "data: [DONE]\n\n"
    
    from fastapi.responses import StreamingResponse
    return StreamingResponse(token_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")