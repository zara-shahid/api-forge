"""
Per-api_id dynamic Swagger docs.

Instead of one generic catch-all route for every generated API, each
api_id gets its own small FastAPI sub-application with real, individual
routes for its entities. Real routes are what let FastAPI generate real,
correct interactive Swagger docs — a single generic wildcard route can't
produce meaningful per-entity documentation.
"""

from fastapi import FastAPI, HTTPException, Body

from app.models.schemas import GeneratedAPI, RouteSpec
from app.serving.store import get_records, persist_records


def _next_id(records: list[dict]) -> int:
    existing_ids = [r.get("id", 0) for r in records if isinstance(r.get("id"), int)]
    return (max(existing_ids) + 1) if existing_ids else 1


def _make_handler(api_id: str, route: RouteSpec):
    """Build the actual endpoint function for one RouteSpec.

    FastAPI inspects each handler's signature to know whether it expects
    a path param like `id` — so list/create take none, get_one/update/
    delete declare `id: str` and FastAPI wires it up automatically from
    the {id} in the route path.
    """
    entity = route.entity

    if route.behavior == "list":
        async def handler():
            return get_records(api_id, entity)
        return handler

    if route.behavior == "get_one":
        async def handler(id: str):
            for r in get_records(api_id, entity):
                if str(r.get("id")) == str(id):
                    return r
            raise HTTPException(404, f"{entity} with id {id} not found")
        return handler

    if route.behavior == "create":
        async def handler(body: dict = Body(...)):
            if not isinstance(body, dict):
                raise HTTPException(400, "Request body must be a JSON object")
            records = get_records(api_id, entity)
            new_record = dict(body)
            new_record["id"] = _next_id(records)
            records.append(new_record)
            persist_records(api_id, entity)
            return new_record
        return handler

    if route.behavior == "update":
        async def handler(id: str, body: dict = Body(...)):
            if not isinstance(body, dict):
                raise HTTPException(400, "Request body must be a JSON object")
            for r in get_records(api_id, entity):
                if str(r.get("id")) == str(id):
                    original_id = r.get("id")
                    r.update(body)
                    r["id"] = original_id
                    persist_records(api_id, entity)
                    return r
            raise HTTPException(404, f"{entity} with id {id} not found")
        return handler

    if route.behavior == "delete":
        async def handler(id: str):
            records = get_records(api_id, entity)
            for i, r in enumerate(records):
                if str(r.get("id")) == str(id):
                    records.pop(i)
                    persist_records(api_id, entity)
                    return {"deleted": True, "id": id}
            raise HTTPException(404, f"{entity} with id {id} not found")
        return handler

    raise ValueError(f"Unknown behavior: {route.behavior}")


def build_docs_subapp(generated: GeneratedAPI) -> FastAPI:
    """Build a FastAPI sub-app with real routes for one generated API.

    Mount this at /api/{api_id} in main.py — its own /docs page becomes
    /api/{api_id}/docs automatically, since FastAPI mounts inherit the
    prefix they're mounted under.
    """
    sub_app = FastAPI(
        title=generated.title,
        description=f"Auto-generated API — {len(generated.entities)} entities, {len(generated.routes)} routes",
    )

    for route in generated.routes:
        handler = _make_handler(generated.api_id, route)
        sub_app.add_api_route(
            path=route.path,
            endpoint=handler,
            methods=[route.method],
            name=f"{route.behavior}_{route.entity}",
            summary=f"{route.behavior.replace('_', ' ').title()} {route.entity}",
        )

    return sub_app