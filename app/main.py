"""
API-Forge — FastAPI entry point.

Run with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.chains.schema_chain import generate_entities
from app.chains.seed_chain import generate_seed_data
from app.chains.route_chain import build_default_crud_routes
from app.models.schemas import GeneratedAPI
from app.serving.router import router as dynamic_router
from app.serving.store import save_generated_api
from app.utils.ids import new_api_id

app = FastAPI(title="API-Forge")

# Loosen CORS for local hackathon dev — tighten before any public deploy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dynamic_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/generate")
async def generate(prompt: str):
    """
    End-to-end pipeline: prompt -> entities -> routes -> seed data
    -> stored + ready to serve at /api/{api_id}/...

    TODO (Day 6): wrap this in try/except per chain step, and add the
    retry-once logic mentioned in schema_chain.py so a single malformed
    generation doesn't 500 mid-demo.
    """
    entities = generate_entities(prompt)
    routes = build_default_crud_routes(entities)  # swap for route_chain.generate_routes() once tuned
    seed_data = generate_seed_data(entities)

    api_id = new_api_id()
    generated = GeneratedAPI(
        api_id=api_id,
        title=prompt[:60],
        entities=entities,
        routes=routes,
    )
    save_generated_api(generated, seed_data)

    return {
        "api_id": api_id,
        "docs_url": f"/api/{api_id}/docs",
        "entity_count": len(entities),
        "route_count": len(routes),
    }
