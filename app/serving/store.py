"""
Generated API store — SQLite-backed with an in-memory cache for fast reads.

Each api_id stays isolated: one apis row + entity_records rows per api_id.
"""

import json

from app.models.schemas import EntitySpec, GeneratedAPI, RouteSpec
from app.serving.database import get_conn, init_db

# Hot cache — loaded from SQLite on startup
GENERATED_APIS: dict[str, GeneratedAPI] = {}
STORE: dict[str, dict[str, list[dict]]] = {}


def load_all_into_memory() -> None:
    """Hydrate cache from SQLite — called once on server startup."""
    GENERATED_APIS.clear()
    STORE.clear()

    with get_conn() as conn:
        for row in conn.execute("SELECT * FROM apis ORDER BY created_at"):
            generated = GeneratedAPI(
                api_id=row["api_id"],
                title=row["title"],
                entities=[EntitySpec.model_validate(e) for e in json.loads(row["entities_json"])],
                routes=[RouteSpec.model_validate(r) for r in json.loads(row["routes_json"])],
            )
            GENERATED_APIS[generated.api_id] = generated
            STORE[generated.api_id] = {}

        for row in conn.execute("SELECT api_id, entity_name, records_json FROM entity_records"):
            api_id = row["api_id"]
            if api_id in STORE:
                STORE[api_id][row["entity_name"]] = json.loads(row["records_json"])


def save_generated_api(generated: GeneratedAPI, seed_data: dict[str, list[dict]]) -> None:
    GENERATED_APIS[generated.api_id] = generated
    STORE[generated.api_id] = seed_data

    with get_conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO apis (api_id, title, prompt, entities_json, routes_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                generated.api_id,
                generated.title,
                generated.title,
                json.dumps([e.model_dump() for e in generated.entities]),
                json.dumps([r.model_dump() for r in generated.routes]),
            ),
        )
        for entity_name, records in seed_data.items():
            conn.execute(
                """
                INSERT OR REPLACE INTO entity_records (api_id, entity_name, records_json)
                VALUES (?, ?, ?)
                """,
                (generated.api_id, entity_name, json.dumps(records)),
            )


def persist_records(api_id: str, entity_name: str) -> None:
    """Write entity records back to SQLite after create/update/delete."""
    records = STORE.get(api_id, {}).get(entity_name, [])
    with get_conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO entity_records (api_id, entity_name, records_json)
            VALUES (?, ?, ?)
            """,
            (api_id, entity_name, json.dumps(records)),
        )


def get_generated_api(api_id: str) -> GeneratedAPI | None:
    return GENERATED_APIS.get(api_id)


def get_records(api_id: str, entity_name: str) -> list[dict]:
    return STORE.get(api_id, {}).get(entity_name, [])


def list_generated_apis() -> list[GeneratedAPI]:
    return list(GENERATED_APIS.values())


def bootstrap_store() -> None:
    init_db()
    load_all_into_memory()
