from flask import Flask, request, jsonify
from datetime import datetime
import json
from typing import Optional

app = Flask(__name__)

# In-memory storage
items_db = {}
item_counter = 1

# Manual validation functions - Lots of boilerplate!
def validate_item_data(data):
    """Manual validation - Error prone and verbose!"""
    errors = []
    
    # Validate name
    if 'name' not in data:
        errors.append("Name is required")
    elif not isinstance(data['name'], str):
        errors.append("Name must be a string")
    elif len(data['name']) < 1 or len(data['name']) > 50:
        errors.append("Name must be between 1 and 50 characters")
    elif not data['name'].strip():
        errors.append("Name cannot be empty")
    
    # Validate price
    if 'price' not in data:
        errors.append("Price is required")
    else:
        try:
            price = float(data['price'])
            if price <= 0:
                errors.append("Price must be greater than 0")
        except (ValueError, TypeError):
            errors.append("Price must be a valid number")
    
    # Validate quantity
    if 'quantity' not in data:
        errors.append("Quantity is required")
    else:
        try:
            quantity = int(data['quantity'])
            if quantity < 1 or quantity > 1000:
                errors.append("Quantity must be between 1 and 1000")
        except (ValueError, TypeError):
            errors.append("Quantity must be a valid integer")
    
    # Validate tags (optional)
    if 'tags' in data:
        if not isinstance(data['tags'], list):
            errors.append("Tags must be a list")
        elif len(data['tags']) > 10:
            errors.append("Maximum 10 tags allowed")
    
    return errors

@app.route('/', methods=['GET'])
def root():
    """Simple root endpoint"""
    return jsonify({
        "message": "Welcome to Flask API",
        "note": "No automatic docs - you need to write them manually!"
    })

@app.route('/items/', methods=['POST'])
def create_item():
    """Create a new item - Lots of manual validation needed!"""
    global item_counter
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Manual validation
    errors = validate_item_data(data)
    if errors:
        return jsonify({"errors": errors}), 400
    
    # Manual data extraction and conversion
    name = data['name'].strip()
    price = float(data['price'])
    quantity = int(data['quantity'])
    tags = data.get('tags', [])
    
    new_item = {
        "id": item_counter,
        "name": name,
        "price": price,
        "quantity": quantity,
        "tags": tags,
        "created_at": datetime.now().isoformat(),
        "total_value": price * quantity
    }
    
    items_db[item_counter] = new_item
    item_counter += 1
    
    return jsonify(new_item), 201

@app.route('/items/', methods=['GET'])
def list_items():
    """List items with manual pagination and filtering"""
    # Manual query parameter parsing and validation
    try:
        skip = int(request.args.get('skip', 0))
        if skip < 0:
            skip = 0
    except ValueError:
        skip = 0
    
    try:
        limit = int(request.args.get('limit', 10))
        if limit < 1 or limit > 100:
            limit = 10
    except ValueError:
        limit = 10
    
    min_price = request.args.get('min_price')
    if min_price:
        try:
            min_price = float(min_price)
        except ValueError:
            return jsonify({"error": "min_price must be a number"}), 400
    
    items = list(items_db.values())
    
    # Manual filtering
    if min_price is not None:
        items = [item for item in items if item["price"] >= min_price]
    
    # Manual pagination
    paginated_items = items[skip:skip + limit]
    
    return jsonify(paginated_items)

@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """Get a specific item"""
    if item_id not in items_db:
        return jsonify({"error": f"Item {item_id} not found"}), 404
    
    return jsonify(items_db[item_id])

@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """Update an item"""
    if item_id not in items_db:
        return jsonify({"error": f"Item {item_id} not found"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Manual validation
    errors = validate_item_data(data)
    if errors:
        return jsonify({"errors": errors}), 400
    
    # Manual update
    name = data['name'].strip()
    price = float(data['price'])
    quantity = int(data['quantity'])
    tags = data.get('tags', [])
    
    updated_item = {
        "id": item_id,
        "name": name,
        "price": price,
        "quantity": quantity,
        "tags": tags,
        "created_at": items_db[item_id]["created_at"],
        "total_value": price * quantity
    }
    
    items_db[item_id] = updated_item
    return jsonify(updated_item)

@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Delete an item"""
    if item_id not in items_db:
        return jsonify({"error": f"Item {item_id} not found"}), 404
    
    del items_db[item_id]
    return jsonify({"message": f"Item {item_id} successfully deleted"})

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "items_count": len(items_db),
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Run with: python flask_app.py
    app.run(host='127.0.0.1', port=5000, debug=False)