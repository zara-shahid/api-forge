"""
Step 1: Schema chain.

Takes a raw natural-language prompt and returns a list of EntitySpec
objects using structured output. This is the first thing to build and
test (Day 2) — get this reliable before touching seed data or routes.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.models.schemas import EntityListWrapper
from app.utils.retry import call_with_retry

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.2,
    api_key=os.environ.get("GROQ_API_KEY"),
    timeout=20,       # Day 8: don't let a stalled call hang the demo
    max_retries=0,    # we do our own retry below, so failures surface immediately
)

structured_llm = llm.with_structured_output(EntityListWrapper)

schema_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You design REST API data models. Given a backend description, "
     "produce 3 to 6 entities with realistic fields and relationships. "
     "Every entity MUST include an 'id' field of type integer as its "
     "first field — this is the primary key and is required with no "
     "exceptions. Keep field names lowercase snake_case. Infer "
     "relationships where the prompt implies them (for example a cart "
     "referencing products), and represent each relationship as both an "
     "entry in that entity's relationships list AND a matching foreign "
     "key field named <related_entity>_id in fields."),
    ("human", "{prompt}"),
])

schema_chain = schema_prompt | structured_llm


def generate_entities(prompt: str):
    """Run the schema chain and return a list of EntitySpec objects.

    Retries once on failure (malformed structured output, timeout, or
    a transient Groq error) before raising, so a single flaky call
    doesn't kill a live demo.
    """
    def _invoke():
        result = schema_chain.invoke({"prompt": prompt})
        return result.entities

    return call_with_retry(
        _invoke,
        attempts=2,
        on_retry=lambda attempt, exc: print(
            f"  schema generation attempt {attempt + 1} failed ({exc!r}), retrying..."
        ),
    )


if __name__ == "__main__":
    # Quick manual check — mirrors scripts/test_schema_chain.py but
    # useful for a fast one-off run while iterating on the prompt.
    test_prompt = "A standard e-commerce system with products, users, a cart, and checkout"
    entities = generate_entities(test_prompt)
    for e in entities:
        print(e.model_dump())