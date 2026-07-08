"""
API-Forge — FastAPI entry point.

Run with:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.chains.schema_chain import generate_entities
from app.chains.seed_chain import generate_seed_data
from app.chains.route_chain import build_default_crud_routes
from app.models.schemas import GeneratedAPI
from app.serving.docs_mount import build_docs_subapp
from app.serving.store import (
    bootstrap_store,
    get_generated_api,
    list_generated_apis,
    save_generated_api,
)
from app.utils.ids import new_api_id


@asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap_store()
    for generated in list_generated_apis():
        sub_app = build_docs_subapp(generated)
        app.mount(f"/api/{generated.api_id}", sub_app)
    yield


app = FastAPI(title="API-Forge", lifespan=lifespan)

# Loosen CORS for local hackathon dev — tighten before any public deploy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/generate")
async def generate(prompt: str):
    """
    End-to-end pipeline: prompt -> entities -> routes -> seed data
    -> stored -> mounted as a real sub-app with its own live Swagger
    docs at /api/{api_id}/docs.
    """
    # Each stage already retries once internally (see call_with_retry in
    # the chain modules). If it still fails after that, surface a clean
    # 503 instead of letting a raw exception 500 out mid-demo.
    try:
        entities = generate_entities(prompt)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Couldn't generate a schema for that prompt, please try again. ({exc})",
        )

    # Deterministic — no LLM call, so nothing to retry or fail here.
    routes = build_default_crud_routes(entities)

    try:
        seed_data = generate_seed_data(entities)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Schema generated but seed data failed, please try again. ({exc})",
        )

    api_id = new_api_id()
    generated = GeneratedAPI(
        api_id=api_id,
        title=prompt[:60],
        entities=entities,
        routes=routes,
    )
    save_generated_api(generated, seed_data)

    # Mount this API's own real routes + docs at /api/{api_id}
    sub_app = build_docs_subapp(generated)
    app.mount(f"/api/{api_id}", sub_app)

    return {
        "api_id": api_id,
        "docs_url": f"/api/{api_id}/docs",
        "entity_count": len(entities),
        "route_count": len(routes),
        "entities": [e.model_dump() for e in entities],
        "prompt": prompt,
    }


@app.get("/apis")
async def list_apis():
    """List every API forged and stored in SQLite."""
    return [
        {
            "api_id": g.api_id,
            "title": g.title,
            "entity_count": len(g.entities),
            "route_count": len(g.routes),
            "docs_url": f"/api/{g.api_id}/docs",
        }
        for g in list_generated_apis()
    ]


@app.get("/apis/{api_id}")
async def get_api(api_id: str):
    """Fetch metadata for a previously forged API (for history reload)."""
    generated = get_generated_api(api_id)
    if not generated:
        raise HTTPException(status_code=404, detail=f"API {api_id} not found")
    return {
        "api_id": generated.api_id,
        "title": generated.title,
        "docs_url": f"/api/{generated.api_id}/docs",
        "entity_count": len(generated.entities),
        "route_count": len(generated.routes),
        "entities": [e.model_dump() for e in generated.entities],
        "prompt": generated.title,
    }