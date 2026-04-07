import httpx
import asyncio
import time
import json

FASTAPI = "http://127.0.0.1:8000"
FLASK   = "http://127.0.0.1:5000"
N       = 200  # concurrent requests for load test

def banner(n, title):
    print(f"\n{'=' * 55}")
    print(f"  {n}. {title}")
    print(f"{'=' * 55}\n")

# ─── 1. Single request ────────────────────────────────────────────────────────

def single_request_test():
    banner(1, "SINGLE REQUEST — /fast")
    for label, url in [("FastAPI", FASTAPI), ("Flask  ", FLASK)]:
        start = time.perf_counter()
        r = httpx.get(f"{url}/fast")
        elapsed = time.perf_counter() - start
        print(f"  {label}  →  {r.json()}  ({elapsed:.4f}s)")

# ─── 2. Concurrency load test ─────────────────────────────────────────────────

async def fetch(client, url):
    return await client.get(url)

async def concurrency_test():
    banner(2, f"CONCURRENCY — {N} simultaneous requests, each sleeps 1s")
    for label, url in [
        ("FastAPI (async, non-blocking)", FASTAPI),
        ("Flask   (threaded, blocking) ", FLASK),
    ]:
        async with httpx.AsyncClient(timeout=30) as client:
            start = time.perf_counter()
            results = await asyncio.gather(*[fetch(client, f"{url}/concurrent-demo") for _ in range(N)])
            elapsed = time.perf_counter() - start
        ok = all(r.status_code == 200 for r in results)
        print(f"  {label}")
        print(f"    {N} requests completed: {ok}")
        print(f"    Wall time : {elapsed:.2f}s  (sequential baseline: {N}.00s)")
        print()

# ─── 3. Pydantic validation ───────────────────────────────────────────────────

def validation_test():
    banner(3, "PYDANTIC VALIDATION — FastAPI /items")

    bad_payloads = [
        ({"name": "",    "price": 10.0, "quantity": 1},              "blank name"),
        ({"name": "hat", "price": -5,   "quantity": 1},              "negative price"),
        ({"name": "hat", "price": 10.0, "quantity": 0},              "zero quantity"),
        ({"name": "hat", "price": 10.0, "quantity": 1, "discount": 1.5}, "discount > 1"),
        ({"price": 10.0, "quantity": 1},                              "missing name"),
        ({
            "name": "hat", "price": 10.0, "quantity": 1,
            "ship_to": {"street": "123 Main", "city": "Austin", "zip_code": "ABCDE"}
        }, "bad nested ZIP"),
    ]

    print("  — Invalid payloads (all should return 422) —\n")
    for payload, reason in bad_payloads:
        r = httpx.post(f"{FASTAPI}/items", json=payload)
        errors = r.json().get("detail", r.json())
        print(f"  [{reason}]")
        print(f"    Status : {r.status_code}")
        print(f"    Errors : {json.dumps(errors, indent=6)}")
        print()

    print("  — Valid payload —\n")
    good = {
        "name": "  Fancy Hat  ",
        "price": 29.99,
        "quantity": 3,
        "tags": ["sale", "headwear"],
        "discount": 0.1,
        "ship_to": {"street": "123 Main St", "city": "Austin", "zip_code": "78701"}
    }
    r = httpx.post(f"{FASTAPI}/items", json=good)
    print(f"  Status  : {r.status_code}")
    print(f"  Response: {json.dumps(r.json(), indent=4)}")

# ─── 4. Docs reminder ────────────────────────────────────────────────────────

def docs_reminder():
    banner(4, "AUTO-GENERATED DOCS (no extra code required)")
    print("  Swagger UI  →  http://127.0.0.1:8000/docs")
    print("  ReDoc       →  http://127.0.0.1:8000/redoc")
    print("  OpenAPI JSON→  http://127.0.0.1:8000/openapi.json")
    print()
    print("  Flask equivalent: install flask-smorest or flasgger,")
    print("  write YAML/decorators manually, keep them in sync by hand.")
    print()
    print("  ✅ FastAPI generates all of the above from your code — always in sync.")

# ─── Main ─────────────────────────────────────────────────────────────────────

async def main():
    single_request_test()
    await concurrency_test()
    validation_test()
    docs_reminder()

asyncio.run(main())

