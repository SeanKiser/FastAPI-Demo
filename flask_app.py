from flask import Flask, request, jsonify
import time

app = Flask(__name__)


@app.route("/fast")
def fast():
    return jsonify({"message": "Flask response ⚡"})


@app.route("/slow")
def slow():
    time.sleep(1)  # ❌ Blocks the entire thread
    return jsonify({"message": "Flask slow endpoint 🐢 (blocking)"})


@app.route("/items", methods=["POST"])
def create_item():
    data = request.get_json()

    # ❌ Manual validation — verbose, brittle, no docs generated
    try:
        name = str(data["name"])
        if not name.strip():
            raise ValueError("name cannot be blank")
        price = float(data["price"])
        if price < 0:
            raise ValueError("price must be >= 0")
        quantity = int(data["quantity"])
        if quantity < 1:
            raise ValueError("quantity must be >= 1")
        tags = data.get("tags", [])
        if not isinstance(tags, list):
            raise ValueError("tags must be a list")
        discount = data.get("discount")
        if discount is not None and not (0 <= float(discount) <= 1):
            raise ValueError("discount must be between 0 and 1")
    except (KeyError, TypeError) as e:
        return jsonify({"error": f"Missing or invalid field: {e}"}), 422
    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    total = price * quantity
    discounted = round(total * (1 - float(discount)), 2) if discount else None

    return jsonify({
        "message": "Manually validated ⚠️",
        "item": {"name": name, "price": price, "quantity": quantity, "tags": tags},
        "total": round(total, 2),
        "discounted_total": discounted
    })


@app.route("/concurrent-demo")
def concurrent_demo():
    time.sleep(1)
    return jsonify({"message": "done"})


if __name__ == "__main__":
    # threaded=True required just to handle multiple connections at all
    app.run(port=5000, threaded=True)

