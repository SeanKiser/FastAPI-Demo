import httpx
import time

fastapi_url = "http://127.0.0.1:8000"
flask_url = "http://127.0.0.1:5000"

def test(name, url):
    start = time.time()
    r = httpx.get(url)
    end = time.time()

    print(f"{name}")
    print("Response:", r.json())
    print("Time:", round(end - start, 4), "seconds")
    print("-" * 40)


if __name__ == "__main__":
    print("FASTAPI TEST")
    test("FastAPI /fast", f"{fastapi_url}/fast")
    test("FastAPI /slow", f"{fastapi_url}/slow")

    print("\nFLASK TEST")
    test("Flask /fast", f"{flask_url}/fast")
    test("Flask /slow", f"{flask_url}/slow")