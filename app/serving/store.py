"""
In-memory store holding every generated API.

Kept deliberately dumb: two dicts keyed by api_id. This is what makes
each generated API isolated from every other one — a bug or a bad
generation in one api_id can never bleed into another.
"""

from app.models.schemas import GeneratedAPI

# api_id -> GeneratedAPI (entities + routes + metadata)
GENERATED_APIS: dict[str, GeneratedAPI] = {}

# api_id -> { entity_name: [record, record, ...] }
STORE: dict[str, dict[str, list[dict]]] = {}


def save_generated_api(generated: GeneratedAPI, seed_data: dict[str, list[dict]]) -> None:
    GENERATED_APIS[generated.api_id] = generated
    STORE[generated.api_id] = seed_data


def get_generated_api(api_id: str) -> GeneratedAPI | None:
    return GENERATED_APIS.get(api_id)


def get_records(api_id: str, entity_name: str) -> list[dict]:
    return STORE.get(api_id, {}).get(entity_name, [])
