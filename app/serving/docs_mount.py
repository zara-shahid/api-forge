"""
Per-api_id dynamic Swagger docs.

Day 7 task: mount a separate FastAPI sub-application per api_id via
app.mount(), with its OpenAPI schema built dynamically from the stored
EntitySpec list, so each generated API gets its own clean
/api/{api_id}/docs URL.
"""

from fastapi import FastAPI

from app.models.schemas import GeneratedAPI


def build_docs_subapp(generated: GeneratedAPI) -> FastAPI:
    """Build a small FastAPI sub-app whose only job is to expose
    Swagger docs for one generated API's entities and routes.

    TODO:
      1. Create `sub_app = FastAPI(title=generated.title)`
      2. For each RouteSpec, register a matching route on sub_app so
         FastAPI can introspect it into an OpenAPI schema (these routes
         can just delegate to the same execute() logic in router.py,
         or even just be documentation stubs if you want docs and
         serving fully decoupled).
      3. Return sub_app so it can be mounted in main.py:
         app.mount(f"/api/{generated.api_id}", sub_app)
    """
    sub_app = FastAPI(
        title=generated.title,
        description=f"Auto-generated API — {len(generated.entities)} entities",
    )

    # TODO: register routes on sub_app here so /docs reflects them

    return sub_app
