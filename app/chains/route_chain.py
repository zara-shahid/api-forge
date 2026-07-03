"""
Step 3: Route spec chain.

Takes the entity list and generates a standard CRUD route set per
entity (list, get_one, create, update, delete), plus any special
routes the prompt implies (e.g. a checkout endpoint).
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.models.schemas import EntitySpec, RouteListWrapper
from app.utils.retry import call_with_retry

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.2,
    api_key=os.environ.get("GROQ_API_KEY"),
    timeout=20,
    max_retries=0,
)

structured_llm = llm.with_structured_output(RouteListWrapper)

route_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You design REST API routes. For each entity given, produce the "
     "standard CRUD routes: list, get_one, create, update, delete. "
     "Use plural entity names in paths (e.g. /products, /products/{id}). "
     "Add special routes only if the entity clearly implies one beyond "
     "plain CRUD (e.g. a checkout_result entity might just need list "
     "and get_one, not full CRUD)."),
    ("human", "Entities:\n{entities}"),
])

route_chain = route_prompt | structured_llm


def generate_routes(entities: list[EntitySpec]):
    """Run the route chain and return a list of RouteSpec objects.

    Fallback note: if you want a zero-LLM-call guarantee for routes,
    you can build standard CRUD routes deterministically in Python
    instead of calling the model at all — the model call only earns
    its keep for the "special route" cases (see Section 7 of the guide).
    """
    entities_text = "\n".join(e.model_dump_json() for e in entities)

    def _invoke():
        result = route_chain.invoke({"entities": entities_text})
        return result.routes

    return call_with_retry(
        _invoke,
        attempts=2,
        on_retry=lambda attempt, exc: print(
            f"  route generation attempt {attempt + 1} failed ({exc!r}), retrying..."
        ),
    )


def build_default_crud_routes(entities: list[EntitySpec]):
    """Deterministic fallback: standard CRUD routes with no LLM call.

    Useful during development so you're not burning API calls just to
    test the serving layer, and as a safe fallback if the route chain
    fails mid-demo.
    """
    from app.models.schemas import RouteSpec

    routes = []
    for e in entities:
        routes.append(RouteSpec(method="GET", path=f"/{e.plural}", entity=e.name, behavior="list"))
        routes.append(RouteSpec(method="GET", path=f"/{e.plural}/{{id}}", entity=e.name, behavior="get_one"))
        routes.append(RouteSpec(method="POST", path=f"/{e.plural}", entity=e.name, behavior="create"))
        routes.append(RouteSpec(method="PUT", path=f"/{e.plural}/{{id}}", entity=e.name, behavior="update"))
        routes.append(RouteSpec(method="DELETE", path=f"/{e.plural}/{{id}}", entity=e.name, behavior="delete"))
    return routes


if __name__ == "__main__":
    from app.chains.schema_chain import generate_entities

    test_prompt = "A hotel booking system with rooms, guests, and reservations"
    entities = generate_entities(test_prompt)
    routes = build_default_crud_routes(entities)
    for r in routes:
        print(r.model_dump())