# TRETTER — Hybrid RAG Shopping Assistant

An AI shopping assistant over the TRETTER shoe catalog (7,476 products) with
**two always-on search modes**:

- **Text search (Corrective RAG)** — type a query; an LLM rewrites it, a FAISS
  text index retrieves candidates, and **hard filters** (price / category /
  in-stock) refine them. Vectors only *rank* — price and category are enforced
  by filters, never guessed by the embedding.
- **Search by photo (lead-gated)** — upload a photo of a shoe (e.g. one that's
  out of stock nearby); the system embeds it with a multimodal model and returns
  visually similar **in-stock** products. Before this runs, the user must enter
  **name, email, phone**, which are saved as a lead.

## Why two indexes

Text and image are different vector spaces. One product becomes one chunk,
bound by `product_id`, feeding two indexes:

| Index | Model | Mode |
|---|---|---|
| `text_index.faiss` | Titan Text V2 (1024-d) | text query |
| `image_index.faiss` | Titan Multimodal (1024-d) | uploaded photo |

Both share `product_id`, so a photo match returns the full product card.

## Pipeline / build order

```
../tretter_products_en.json   (scraped + translated products)
        │
        ▼  build_chunks.py
product_chunks.json           (one chunk per product, DE+EN + metadata)
        │
        ├─ build_text_index.py   → text_index.faiss  + text_metadata.json
        └─ build_image_index.py  → image_index.faiss + image_metadata.json
        │
        ▼  main.py (FastAPI)
   /chat            → text mode (CRAG + hard filters)
   /search-by-image → photo mode (lead gate → DynamoDB)
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # then fill in AWS keys
```

### Bedrock models (enable in the Bedrock console, your region)
- `amazon.titan-embed-text-v2:0`
- `amazon.titan-embed-image-v1`
- `amazon.nova-pro-v1:0`

### DynamoDB tables (create once)
- **tretter-chat-history** — PK `session_id` (String), SK `timestamp` (Number).
  Enable TTL on attribute `ttl`.
- **tretter-leads** — PK `lead_id` (String), SK `timestamp` (Number).

(If the tables are absent the app still runs; chat history and leads are just
not persisted, and a warning is logged.)

## Build the indexes (one time, resumable)

```powershell
python build_chunks.py
python build_text_index.py     # ~7,476 Titan Text calls
python build_image_index.py    # ~7,476 Titan Multimodal calls
```

Both cache to `*_cache.jsonl`; re-run to resume if interrupted.

## Run

```powershell
uvicorn main:app --reload --port 8000
# open http://localhost:8000
```

## How the "sneakers under €200" case is handled

1. `parse_filters` extracts `category=sneaker`, `max_price=200` from the text.
2. The text embedding retrieves candidates (ranking only).
3. `passes_filters` drops anything that isn't a sneaker or costs > €200.

So embeddings never decide category or price — they only order the results that
already passed the hard filters. This prevents image/text similarity from
leaking in the wrong shoe type or over-budget items.

## Endpoints
- `GET  /` — UI
- `GET  /session` — new session id
- `POST /chat` — `{message, session_id}` → text search
- `POST /search-by-image` — multipart: `image, name, email, phone, session_id`
- `GET  /health` — index + table status
