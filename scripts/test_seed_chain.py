"""
Day 3: run the schema chain, then the seed chain, and print sample
records for a few prompts. Judge the output on realism, not just
correctness — do names, prices, emails, and dates look like real data
or obvious placeholders?

Run with:
    python scripts/test_seed_chain.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.chains.schema_chain import generate_entities
from app.chains.seed_chain import generate_seed_data

TEST_PROMPTS = [
    "A blog platform with posts, authors, and comments",
    "A hotel booking system with rooms, guests, and reservations",
]


def main():
    for prompt in TEST_PROMPTS:
        print(f"\n=== {prompt} ===")
        try:
            entities = generate_entities(prompt)
            seed = generate_seed_data(entities)
            for entity_name, records in seed.items():
                print(f"\n  --- {entity_name} ({len(records)} records) ---")
                for r in records[:3]:
                    print(f"  {r}")
        except Exception as exc:
            print(f"  FAILED: {exc}")


if __name__ == "__main__":
    main()