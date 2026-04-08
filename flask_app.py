from flask import Flask, request, jsonify, Response
import time
import uuid
from datetime import datetime
import threading
import queue

app = Flask(__name__)

# Helper functions (same logic but sync)
def simulate_embedding_sync(text: str):
    """Simulate embedding generation - blocks the entire server"""
    compute_time = min(0.01 * len(text), 0.1)
    time.sleep(compute_time)  # BLOCKING - this is the problem!
    return [float(hash(f"{text}_{i}") % 1000) / 1000 for i in range(384)]

def simulate_generation_sync(prompt: str, max_tokens: int):
    """Simulate LLM generation - blocks the entire server"""
    tokens = []
    for i in range(max_tokens):
        time.sleep(0.01)  # BLOCKING per token
        tokens.append(f"token_{i}")
    return f"Generated response for: '{prompt[:50]}...' using {len(tokens)} tokens"

# Manual validation (error-prone, lots of boilerplate)
def validate_embedding_request(data):
    if not data or 'text' not in data:
        return False, "Missing 'text' field"
    if not isinstance(data['text'], str):
        return False, "'text' must be string"
    if len(data['text']) == 0:
        return False, "'text' cannot be empty"
    if len(data['text']) > 1000:
        return False, "'text' too long (max 1000 chars)"
    return True, None

def validate_generate_request(data):
    if not data or 'prompt' not in data:
        return False, "Missing 'prompt' field"
    if not isinstance(data['prompt'], str):
        return False, "'prompt' must be string"
    if len(data['prompt']) == 0:
        return False, "'prompt' cannot be empty"
    
    max_tokens = data.get('max_tokens', 100)
    if not isinstance(max_tokens, int) or max_tokens < 1 or max_tokens > 500:
        return False, "'max_tokens' must be integer between 1 and 500"
    
    temp = data.get('temperature', 0.7)
    if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
        return False, "'temperature' must be between 0 and 2"
    
    return True, None

@app.route('/embed', methods=['POST'])
def generate_embedding():
    """Generate embedding - but each request blocks all others!"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Manual validation
    data = request.get_json()
    valid, error = validate_embedding_request(data)
    if not valid:
        return jsonify({"error": error}), 400
    
    try:
        embedding = simulate_embedding_sync(data['text'])
        latency_ms = (time.time() - start_time) * 1000
        
        return jsonify({
            "embedding": embedding,
            "dimension": len(embedding),
            "latency_ms": round(latency_ms, 2),
            "request_id": request_id
        })
    except Exception as e:
        return jsonify({"error": f"Embedding failed: {str(e)}"}), 500

@app.route('/generate', methods=['POST'])
def generate_text():
    """Generate text - blocks entire server during generation"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    data = request.get_json()
    valid, error = validate_generate_request(data)
    if not valid:
        return jsonify({"error": error}), 400
    
    try:
        generated = simulate_generation_sync(data['prompt'], data.get('max_tokens', 100))
        latency_ms = (time.time() - start_time) * 1000
        
        return jsonify({
            "generated_text": generated,
            "tokens_generated": data.get('max_tokens', 100),
            "latency_ms": round(latency_ms, 2),
            "request_id": request_id
        })
    except Exception as e:
        return jsonify({"error": f"Generation failed: {str(e)}"}), 500

@app.route('/embed/batch', methods=['POST'])
def batch_embedding():
    """Process batch sequentially - NO concurrency"""
    data = request.get_json()
    if not data or 'texts' not in data:
        return jsonify({"error": "Missing 'texts' field"}), 400
    
    texts = data['texts']
    if not isinstance(texts, list) or len(texts) == 0 or len(texts) > 100:
        return jsonify({"error": "texts must be list of 1-100 items"}), 400
    
    responses = []
    for text in texts:
        start_time = time.time()
        embedding = simulate_embedding_sync(text)
        responses.append({
            "embedding": embedding,
            "dimension": len(embedding),
            "latency_ms": round((time.time() - start_time) * 1000, 2),
            "request_id": str(uuid.uuid4())
        })
    
    return jsonify(responses)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

# Note: No automatic documentation, no streaming support, no async

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=False)