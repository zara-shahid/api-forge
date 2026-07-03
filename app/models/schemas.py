"""
Core Pydantic models for API-Forge.

Every LangChain chain in this project produces output validated against
one of these. Keeping the chains and the serving layer both built on the
same shapes is what keeps generation -> serving reliable end to end.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class FieldSpec(BaseModel):
    name: str
    type: Literal["string", "integer", "float", "boolean", "datetime"]
    required: bool = True
    example: Optional[str | int | float] = None


class EntitySpec(BaseModel):
    name: str          # e.g. "product"
    plural: str         # e.g. "products"
    fields: list[FieldSpec]
    relationships: list[str] = Field(default_factory=list)  # related entity names


class RouteSpec(BaseModel):
    method: Literal["GET", "POST", "PUT", "DELETE"]
    path: str            # e.g. "/products" or "/products/{id}"
    entity: str
    behavior: Literal["list", "get_one", "create", "update", "delete"]


class GeneratedAPI(BaseModel):
    api_id: str
    title: str
    entities: list[EntitySpec]
    routes: list[RouteSpec]


# --- Wrapper models for structured LLM output ---
# with_structured_output() needs a single top-level model per chain call,
# so each chain gets a thin wrapper around the list it actually returns.

class EntityListWrapper(BaseModel):
    entities: list[EntitySpec]


class RouteListWrapper(BaseModel):
    routes: list[RouteSpec]


class SeedRecord(BaseModel):
    entity: str
    records: list[dict]


class SeedDataWrapper(BaseModel):
    data: list[SeedRecord]
