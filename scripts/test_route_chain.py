"""
Day 4: run the schema chain, then build default CRUD routes, and print
them. No LLM call needed for routes — build_default_crud_routes() is
deterministic Python logic over the entities.

Run with:
    python scripts/test_route_chain.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.chains.schema_chain import generate_entities
from app.chains.route_chain import build_default_crud_routes

TEST_PROMPTS = [
    "A blog platform with posts, authors, and comments",
    "A hotel booking system with rooms, guests, and reservations",
]


def main():
    for prompt in TEST_PROMPTS:
        print(f"\n=== {prompt} ===")
        entities = generate_entities(prompt)
        routes = build_default_crud_routes(entities)
        for r in routes:
            print(f"  {r.method:6} {r.path:30} -> {r.entity} ({r.behavior})")


if __name__ == "__main__":
    main()