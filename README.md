# API-Forge

Prompt-to-full-stack mock API engine. Describe a backend in plain English,
get a live, documented, queryable REST API back in seconds.

Built for Next Byte Hacks V3.

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # then paste in your real GROQ_API_KEY
```

## Run

```bash
uvicorn app.main:app --reload
```

Server runs at `http://127.0.0.1:8000`. Check `/health` to confirm it's up.

Open `frontend/index.html` in a browser (or serve it) to use the prompt UI.

## Architecture

TODO: fill in once the pipeline is stable — see the implementation guide
for the full architecture diagram (prompt UI -> /generate -> LangChain
pipeline -> in-memory store -> generic catch-all router -> per-api_id docs).

## Project structure

```
app/
  main.py            FastAPI app + /generate endpoint
  models/schemas.py  Pydantic models shared by chains and serving layer
  chains/            schema_chain, seed_chain, route_chain
  serving/           router, store, docs_mount
  utils/             helpers (id generation, etc.)
frontend/            prompt UI + result screen
scripts/             manual sanity-check scripts (Groq connection, schema chain)
tests/               pytest coverage (optional, not required for submission)
```

## License

MIT
