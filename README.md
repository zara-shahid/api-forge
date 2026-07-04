```markdown
# API-Forge

Turn a single sentence into a fully documented, queryable REST API.

Describe a backend in plain English, e.g. *"a standard e-commerce system with products, users, a cart, and checkout"*, and get back a live, interactive Swagger UI backed by a real running FastAPI server with realistic seed data, in seconds.

Built for Next Byte Hacks V3.

## Why this exists

Frontend teams routinely wait on backend teams to design a schema, seed data, and deploy endpoints just to start building UI. Tools like Mockoon, Beeceptor, and MockingCloud already generate AI-powered mocks, but every one of them needs you to bring an existing OpenAPI spec or existing traffic first.

API-Forge starts from nothing but a sentence. The generation pipeline is also fully visible and inspectable, split into three distinct LangChain steps (schema, seed data, routes) rather than one opaque prompt-to-JSON call, and it produces real FastAPI-native Swagger docs rather than a custom-built dashboard mimicking one.

## How it works

```
Prompt UI
   │  POST /generate { "prompt": "..." }
   ▼
FastAPI Generation Endpoint
   │  invokes
   ▼
LangChain Pipeline
   Step 1: Schema chain   → EntitySpec[] (Pydantic, structured output)
   Step 2: Seed chain     → realistic in-memory records per entity
   Step 3: Route builder  → RouteSpec[] (standard CRUD, no LLM call needed)
   │  writes
   ▼
In-memory store  { api_id: { entities, records, routes } }
   │
   ▼
Per-api_id FastAPI sub-app, mounted at /api/{api_id}
   → real routes for every entity, real auto-generated Swagger docs
   → GET/POST/PUT/DELETE fully implemented (list, get_one, create, update, delete)
```

Each generated API is a fully independent, mounted FastAPI sub-application. This means two different generated APIs can run side by side with zero risk of one interfering with the other, and each gets its own genuine, correct Swagger documentation rather than a shared generic catch-all.

## Tech stack

| Layer | Choice |
|---|---|
| Backend | FastAPI |
| LLM orchestration | LangChain |
| LLM provider | Groq (`llama-3.3-70b-versatile`) |
| Schema validation | Pydantic v2 |
| Data storage | In-memory (no database dependency) |
| Frontend | Plain HTML/CSS/JS |

## Setup

```bash
python -m venv venv
venv\Scripts\Activate.ps1        # Windows PowerShell
# source venv/bin/activate       # macOS/Linux

pip install -r requirements.txt
cp .env.example .env             # then paste in your real GROQ_API_KEY
```

## Run

```bash
uvicorn app.main:app --reload
```

Server runs at `http://127.0.0.1:8000`. Confirm it's up:

```bash
curl http://127.0.0.1:8000/health
```

Open `frontend/index.html` in a browser to use the prompt UI, or generate directly:

```bash
curl -X POST "http://127.0.0.1:8000/generate?prompt=A blog platform with posts, authors, and comments"
```

This returns an `api_id`. Visit `http://127.0.0.1:8000/api/{api_id}/docs` for a live, interactive Swagger UI, every endpoint is real and clickable, including "Try it out" against actual seeded data.

## Example prompts

| Prompt | Entities generated |
|---|---|
| A standard e-commerce backend with products, users, a shopping cart, and a stripe checkout simulation | product, user, cart, order, stripe_payment |
| A blog platform with posts, authors, and comments | post, author, comment |
| A hotel booking system with rooms, guests, and reservations | room, guest, reservation |
| A social feed with users, posts, and likes | user, post, like |

The pipeline isn't limited to these, any plain-English backend description works.

## Reliability

Groq's structured-output parsing occasionally fails on longer completions even when the underlying data is fine. Every chain call is wrapped in automatic retry logic (`app/utils/retry.py`) that retries up to 3 times before surfacing a clean error, so a single transient failure doesn't break generation.

## Project structure

```
app/
  main.py              FastAPI app, /generate endpoint, mounts per-api_id sub-apps
  models/schemas.py    Pydantic models shared across chains and serving layer
  chains/
    schema_chain.py    Prompt -> entities (LLM, structured output)
    seed_chain.py      Entities -> realistic seed records (LLM, structured output, retried)
    route_chain.py     Entities -> standard CRUD routes (deterministic, no LLM call)
  serving/
    docs_mount.py      Builds a real FastAPI sub-app with live routes + Swagger docs per api_id
    store.py           In-memory storage, isolated per api_id
  utils/
    retry.py           Shared retry wrapper for LLM calls
    ids.py             api_id generation
frontend/
  index.html           Prompt screen (Screen 1) + result screen (Screen 2)
  app.js               Calls the live backend, renders real stats/entities from the response
  style.css            Forge & Blueprint design system
scripts/                Manual test scripts for each pipeline stage
tests/                  Pytest scaffolding
```

## Known limitations

- Data is in-memory only. Restarting the server clears every generated API. This is intentional, it keeps the demo dependency-free and instantly resettable.
- Route generation defaults to standard CRUD per entity rather than calling the LLM for route design, this is a deliberate reliability choice, not a missing feature.

```