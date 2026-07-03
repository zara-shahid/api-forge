"""
Day 8: fire 5 varied prompts at the live /generate endpoint back to
back and confirm every single one succeeds without manual
intervention. This is the actual acceptance test for Day 8 -- if this
script doesn't print ALL PASSED, Day 8 isn't done yet.

Requires the server to already be running:
    uvicorn app.main:app --reload

Run with:
    python scripts/test_reliability.py
"""

import json
import time
import urllib.request
import urllib.parse
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

TEST_PROMPTS = [
    "A standard e-commerce backend with products, users, a shopping cart, and a stripe checkout simulation",
    "A blog platform with posts, authors, and comments",
    "A hotel booking system with rooms, guests, and reservations",
    "A social feed with users, posts, and likes",
    "A task management app with projects, tasks, and assignees",
]


def check_health():
    try:
        urllib.request.urlopen(f"{BASE_URL}/health", timeout=5)
        return True
    except Exception:
        return False


def run_one(prompt: str):
    url = f"{BASE_URL}/generate?{urllib.parse.urlencode({'prompt': prompt})}"
    req = urllib.request.Request(url, method="POST")

    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            elapsed = time.time() - start
            data = json.loads(resp.read())
            return {
                "ok": True,
                "elapsed": elapsed,
                "api_id": data.get("api_id"),
                "entity_count": data.get("entity_count"),
                "route_count": data.get("route_count"),
            }
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start
        body = e.read().decode(errors="replace")
        return {"ok": False, "elapsed": elapsed, "error": f"HTTP {e.code}: {body}"}
    except Exception as exc:
        elapsed = time.time() - start
        return {"ok": False, "elapsed": elapsed, "error": repr(exc)}


def main():
    if not check_health():
        print(f"Server not reachable at {BASE_URL}.")
        print("Start it first:  uvicorn app.main:app --reload")
        return

    print(f"Running {len(TEST_PROMPTS)} prompts against {BASE_URL}/generate ...\n")

    results = []
    for i, prompt in enumerate(TEST_PROMPTS, start=1):
        print(f"[{i}/{len(TEST_PROMPTS)}] {prompt}")
        result = run_one(prompt)
        results.append((prompt, result))

        if result["ok"]:
            print(
                f"    OK  {result['elapsed']:.1f}s  "
                f"api_id={result['api_id']}  "
                f"entities={result['entity_count']}  routes={result['route_count']}"
            )
        else:
            print(f"    FAIL  {result['elapsed']:.1f}s  {result['error']}")
        print()

    passed = sum(1 for _, r in results if r["ok"])
    print("=" * 60)
    print(f"{passed}/{len(results)} prompts succeeded")

    if passed == len(results):
        print("ALL PASSED — Day 8 reliability bar met.")
    else:
        print("NOT ALL PASSED — Day 8 hardening still needs work before this is demo-safe.")


if __name__ == "__main__":
    main()