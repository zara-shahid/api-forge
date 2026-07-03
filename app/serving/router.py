"""
Generic catch-all serving layer.

One handler reads the stored RouteSpec list for a given api_id at
request time and performs the matching CRUD behavior against the
in-memory records. This avoids ever mutating the FastAPI app object
dynamically (no setattr route-mounting), which is fragile and hard to
debug live on stage.
"""

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import RouteSpec
from app.serving.store import get_generated_api, get_records

router = APIRouter()


def match_route(routes: list[RouteSpec], path: str, method: str) -> tuple[RouteSpec, dict] | None:
    """Match an incoming (path, method) against the generated route spec.

    Returns (route, path_params) so callers can pull out things like
    the id from a path like /posts/42.
    """
    request_segments = path.split("/")

    for route in routes:
        if route.method != method:
            continue

        route_segments = route.path.strip("/").split("/")
        if len(route_segments) != len(request_segments):
            continue

        path_params = {}
        matched = True
        for route_seg, req_seg in zip(route_segments, request_segments):
            if route_seg.startswith("{") and route_seg.endswith("}"):
                param_name = route_seg[1:-1]
                path_params[param_name] = req_seg
            elif route_seg != req_seg:
                matched = False
                break

        if matched:
            return route, path_params

    return None


def _next_id(records: list[dict]) -> int:
    """Generate the next integer id for a new record.

    Takes the highest existing id and adds 1, rather than just using
    len(records)+1 — that way ids stay unique even after deletes leave
    gaps (e.g. delete id 3 out of 5, then create: len()+1 would collide
    with an id that still exists).
    """
    existing_ids = [r.get("id", 0) for r in records if isinstance(r.get("id"), int)]
    return (max(existing_ids) + 1) if existing_ids else 1


async def execute(route: RouteSpec, api_id: str, path_params: dict, request: Request):
    """Perform the CRUD behavior implied by the matched route."""
    records = get_records(api_id, route.entity)

    if route.behavior == "list":
        return records

    if route.behavior == "get_one":
        record_id = path_params.get("id")
        for r in records:
            if str(r.get("id")) == str(record_id):
                return r
        raise HTTPException(404, f"{route.entity} with id {record_id} not found")

    if route.behavior == "create":
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(400, "Request body must be valid JSON")

        if not isinstance(body, dict):
            raise HTTPException(400, "Request body must be a JSON object")

        new_record = dict(body)
        new_record["id"] = _next_id(records)
        records.append(new_record)
        return new_record

    if route.behavior == "update":
        record_id = path_params.get("id")
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(400, "Request body must be valid JSON")

        if not isinstance(body, dict):
            raise HTTPException(400, "Request body must be a JSON object")

        for r in records:
            if str(r.get("id")) == str(record_id):
                r.update(body)
                r["id"] = r.get("id")  # never let the body overwrite the id
                return r
        raise HTTPException(404, f"{route.entity} with id {record_id} not found")

    if route.behavior == "delete":
        record_id = path_params.get("id")
        for i, r in enumerate(records):
            if str(r.get("id")) == str(record_id):
                records.pop(i)
                return {"deleted": True, "id": record_id}
        raise HTTPException(404, f"{route.entity} with id {record_id} not found")

    raise HTTPException(500, f"Unknown behavior: {route.behavior}")


@router.api_route("/api/{api_id}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def dynamic_handler(api_id: str, path: str, request: Request):
    spec = get_generated_api(api_id)
    if not spec:
        raise HTTPException(404, f"Unknown api_id: {api_id}")

    match = match_route(spec.routes, path, request.method)
    if not match:
        raise HTTPException(404, f"No matching route for {request.method} /{path}")

    route, path_params = match
    return await execute(route, api_id, path_params, request)