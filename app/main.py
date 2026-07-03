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
from app.serving.docs_mount import build_docs_subapp
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
    entities = generate_entities(prompt)
    routes = build_default_crud_routes(entities)
    seed_data = generate_seed_data(entities)

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
    }