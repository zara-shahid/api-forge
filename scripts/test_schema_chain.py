"""
Day 2: run the schema chain against several varied prompts and print
the resulting entities. Eyeball these for sane field names, plausible
types, and reasonable relationship inference before moving to Day 3.

Run with:
    python scripts/test_schema_chain.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.chains.schema_chain import generate_entities

TEST_PROMPTS = [
    "A standard e-commerce backend with products, users, a shopping cart, and a stripe checkout simulation",
    "A blog platform with posts, authors, and comments",
    "A hotel booking system with rooms, guests, and reservations",
    "A social feed with users, posts, and likes",
    "A task management app with projects, tasks, and assignees",
    "A recipe sharing site with recipes, ingredients, and reviews",
]

def main():
    for prompt in TEST_PROMPTS:
        print(f"\n=== {prompt} ===")
        try:
            entities = generate_entities(prompt)
            for e in entities:
                print(f"  {e.name} ({e.plural}): {[f.name for f in e.fields]}")
                if e.relationships:
                    print(f"    relationships: {e.relationships}")
        except Exception as exc:
            print(f"  FAILED: {exc}")


if __name__ == "__main__":
    main()
