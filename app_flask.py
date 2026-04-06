from flask import Flask, request, jsonify
import time

app = Flask(__name__)


@app.route("/fast")
def fast():
    return jsonify({"message": "Flask response ⚡"})


@app.route("/slow")
def slow():
    time.sleep(1)
    return jsonify({"message": "Flask slow endpoint 🐢 (blocking)"})


@app.route("/items", methods=["POST"])
def create_item():
    data = request.get_json()

    # ❌ Manual validation (error-prone)
    try:
        name = data["name"]
        price = float(data["price"])
        quantity = int(data["quantity"])
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({
        "message": "Manually validated (more bug-prone)",
        "item": data,
        "total": price * quantity
    })

if __name__ == "__main__":
    app.run(port=5000)