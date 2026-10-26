# TRETTER AI Shopping Assistant

> **Live:** https://d31qqwhgzn5qcm.cloudfront.net

A production-deployed, AI-powered shoe shopping assistant built on a scraped and translated product catalog from [tretter.com](https://tretter.com) — **7,476 products**. Two independent search modes are always available: natural-language text search with hard filters (Corrective RAG), and reverse image / photo search gated behind a lead-capture form.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Search Modes](#search-modes)
3. [Data Pipeline](#data-pipeline)
4. [Backend (main.py)](#backend-mainpy)
5. [Frontend (static/index.html)](#frontend-staticindexhtml)
6. [Local Setup](#local-setup)
7. [Building the Indexes](#building-the-indexes)
8. [Running Locally](#running-locally)
9. [Deployment Guide](#deployment-guide)
10. [Environment Variables](#environment-variables)
11. [Utility Scripts](#utility-scripts)
12. [Known Issues & Decisions](#known-issues--decisions)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CloudFront CDN                           │
│          https://d31qqwhgzn5qcm.cloudfront.net                  │
│          Distribution: E104RJTSTWBCNC                           │
│          CachingDisabled | AllViewerExceptHostHeader             │
└─────────────────────┬───────────────────────────────────────────┘
                      │  HTTPS (all methods)
┌─────────────────────▼───────────────────────────────────────────┐
│                   AWS Lambda Function URL                        │
│           tretter-shopping-assistant                             │
│           3008 MB RAM | 120 s timeout | AuthType=NONE            │
│           FastAPI + Mangum (ASGI → Lambda adapter)              │
└──────┬──────────────┬──────────────────┬────────────────────────┘
       │              │                  │
┌──────▼──────┐ ┌─────▼──────┐  ┌───────▼───────────────────────┐
│  DynamoDB   │ │  DynamoDB  │  │      Amazon Bedrock            │
│  tretter-   │ │  tretter-  │  │  us-east-1                    │
│  chat-      │ │  leads     │  │                               │
│  history    │ │            │  │  • Titan Text V2 (embed)      │
│  TTL 7 days │ │            │  │  • Titan Multimodal (embed)   │
└─────────────┘ └────────────┘  │  • Nova Pro (LLM)             │
                                └───────────────────────────────┘

  FAISS indexes (loaded into Lambda memory at cold start):
    text_index.faiss   — Titan Text V2 1024-dim IndexFlatIP (cosine)
    image_index.faiss  — Titan Multimodal 1024-dim IndexFlatIP (cosine)
    product_chunks.json — ground-truth product data (EN + DE)
```

### Two FAISS Indexes

| Artifact | Embedding model | Dimension | Index type | Built from |
|---|---|---|---|---|
| `text_index.faiss` | `amazon.titan-embed-text-v2:0` (Titan Text V2) | 1024 | `IndexFlatIP` (cosine, normalized) | English product text chunks |
| `image_index.faiss` | `amazon.titan-embed-image-v1` (Titan Multimodal G1) | 1024 | `IndexFlatIP` (cosine, L2-normalized) | Product images downloaded from tretter.com |

Both indexes are keyed by `product_id` (SKU when available, otherwise SHA-1 of the product URL). The shared key means a photo match can return the complete product card from `product_chunks.json`.

---

## Search Modes

### Mode 1 — Text Search (Corrective RAG / CRAG)

```
User query
    │
    ▼  detect_intent()
    │  (greetings/small-talk → conversational_reply(), skip pipeline)
    │
    ▼  rewrite_query()  — Nova Pro rewrites for shoe attributes
    │  (type, gender, color, material, brand, price range)
    │
    ▼  embed query  — Titan Text V2
    │
    ▼  FAISS text_index.search(k=20)
    │
    ▼  parse_filters()  — extract max_price, min_price, category keywords, in_stock flag
    ▼  passes_filters()  — HARD FILTER: price (float), category keyword match, availability=InStock
    │  (runs AFTER retrieval, BEFORE response)
    │  (price and category enforced by code, NOT by embedding)
    │
    ▼  generate_reply()  — Nova Pro
       System prompt: only mention what was asked, never hallucinate,
       state count, ≤ 3 sentences, match requested language (DE/EN)
```

**Why hard filters?** Vectors rank by similarity — they do not enforce budget or shoe type. Without `passes_filters()`, a query for "sneakers under €200" could return €350 boots ranked highly because their embeddings are close. Filters prevent this: category and price are checked by Python code against the product metadata, not inferred from the vector.

### Mode 2 — Image / Photo Search (Lead-Gated)

```
User uploads photo
    │
    ▼  Contact gate: name + email (regex validated) + phone REQUIRED
    │  → lead saved to DynamoDB tretter-leads (PK: lead_id, SK: timestamp)
    │
    ▼  Image format normalization
    │  AVIF / HEIC / any format → JPEG via Pillow + pillow-avif-plugin
    │
    ▼  embed image — Titan Multimodal Embeddings G1
    │
    ▼  FAISS image_index.search(k=20)
    │
    ▼  force_in_stock=True filter
    │
    ▼  Return visually similar in-stock products
```

The lead gate serves a dual purpose: it captures warm leads (users motivated enough to upload a photo) and deters abuse of the image embedding endpoint.

---

## Data Pipeline

Run these scripts **once**, in order, to build the indexes from scratch. Each step is resumable.

```
tretter.com (sitemap)
    │
    ▼  1. tretter_scraper.py
    │     Playwright + BeautifulSoup
    │     69 product sitemaps → 7,681 URLs
    │     JSON-LD extraction, image download
    │     Crash-safe JSONL output
    │
    ▼  tretter_products_raw.jsonl  (raw, German)
    │
    ▼  2. translate.py
    │     German → English via Amazon Nova Pro (Bedrock converse API)
    │     Field-by-field translation with cache (translation_cache.json)
    │     SKIPS product names (brand model codes — "Dublin 2.0", "Arch-E")
    │     Outputs: tretter_products_en.json + tretter_products_en.csv
    │
    ▼  tretter_products_en.json
    │
    ▼  3. build_chunks.py
    │     Reads tretter_products_en.json
    │     One chunk per product
    │     Assigns product_id: SKU if available, else sha1(URL)
    │     Fields per chunk: product_id, text (EN), text_de (DE), metadata
    │     Output: product_chunks.json
    │
    ▼  product_chunks.json
    │
    ├── 4. build_text_index.py
    │       Titan Text V2 embeddings (1024-dim)
    │       Cached to text_embeddings_cache.jsonl (crash-safe resume)
    │       Normalizes vectors → IndexFlatIP (cosine similarity)
    │       Output: text_index.faiss + text_metadata.json
    │
    └── 5. build_image_index.py
            Reads local image files: images/<sku>.jpg
            Titan Multimodal G1 embeddings (1024-dim)
            Cached to image_embeddings_cache.jsonl (crash-safe resume)
            L2-normalizes vectors → IndexFlatIP (cosine similarity)
            Output: image_index.faiss + image_metadata.json
```

### Pipeline Details

| Script | Input | Output | Notes |
|---|---|---|---|
| `tretter_scraper.py` | tretter.com sitemaps | `tretter_products_raw.jsonl`, `images/` | Playwright browser, JSON-LD, crash-safe |
| `translate.py` | `tretter_products_raw.jsonl` | `tretter_products_en.json`, `.csv` | Nova Pro via Bedrock; caches to `translation_cache.json`; skips product names |
| `build_chunks.py` | `tretter_products_en.json` | `product_chunks.json` | One chunk/product; `product_id` = SKU or sha1(URL) |
| `build_text_index.py` | `product_chunks.json` | `text_index.faiss`, `text_metadata.json` | ~7,476 Titan Text V2 API calls; resumable |
| `build_image_index.py` | `images/<sku>.jpg` | `image_index.faiss`, `image_metadata.json` | ~7,476 Titan Multimodal API calls; resumable |

**Why product names are NOT translated:** Nova Pro hallucinated marketing paragraphs when given bare brand model codes like "Dublin 2.0" or "Arch-E" as translation input. The fix: `name_en = name` — product names are copied verbatim, not sent to the translation model.

---

## Backend (main.py)

### Stack
- **FastAPI** — async REST API
- **Mangum** — ASGI-to-Lambda adapter (wraps the FastAPI app as a Lambda handler)
- **faiss-cpu 1.7.4** — vector similarity search (pre-built binary, installed separately)
- **boto3** — AWS Bedrock + DynamoDB

### Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Serves `static/index.html` (the UI) |
| `GET` | `/session` | Returns a new `session_id` (UUID) |
| `POST` | `/chat` | Text search (CRAG pipeline) |
| `POST` | `/search-by-image` | Multipart: `image`, `name`, `email`, `phone`, `session_id` |
| `GET` | `/health` | Index load status + DynamoDB table status |

### `/chat` Request Body

```json
{
  "message": "sneakers under 200 euros",
  "session_id": "uuid",
  "lang": "de"
}
```

The `lang` field (`"de"` or `"en"`) is sent with every request. Nova Pro's system prompt explicitly instructs it to reply in that language — this is not left to model inference.

### DynamoDB Tables

| Table | PK | SK | TTL attribute | Purpose |
|---|---|---|---|---|
| `tretter-chat-history` | `session_id` (String) | `timestamp` (Number) | `ttl` (7 days) | Per-session conversation history |
| `tretter-leads` | `lead_id` (String) | `timestamp` (Number) | — | Image search leads (name, email, phone) |

### Bedrock Clients

```python
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
```

| Purpose | Model ID |
|---|---|
| Text embedding | `amazon.titan-embed-text-v2:0` |
| Image embedding | `amazon.titan-embed-image-v1` |
| Query rewrite + reply generation | `amazon.nova-pro-v1:0` |

### Lazy Index Loading

Indexes are **not** loaded at module import time. They load on the first request. This is required because Lambda's init phase has a **10-second limit** — loading two FAISS indexes plus `product_chunks.json` at module init exceeded it. With lazy loading, cold-start index load takes ~4 seconds inside the first request (within Lambda's 120 s function timeout), not during the init phase.

### CRAG Pipeline (Text Mode)

1. **`detect_intent()`** — Classifies the message. Greetings and chat phrases route to `conversational_reply()` and skip the full pipeline.
2. **`rewrite_query()`** — Nova Pro rewrites the user query to be richer in shoe attributes: type, gender, color, material, brand, price range.
3. **`search_text()`** — Embeds the rewritten query with Titan Text V2, searches `text_index.faiss`.
4. **`parse_filters()`** — Extracts `max_price`, `min_price`, category keywords, `in_stock` flag from the original user message.
5. **`passes_filters()`** — Applies hard filters: price as float comparison, category keyword match, `availability == "InStock"`.
6. **`generate_reply()`** — Nova Pro generates a reply. System prompt enforces: only mention what was asked, never hallucinate, state the count, ≤ 3 sentences, match `lang`.

---

## Frontend (static/index.html)

### Design System

Faithfully mirrors tretter.com's visual identity:

| Property | Value |
|---|---|
| Background / primary | `#111111` (near-black) |
| Text / borders | White, `1px` hairline borders |
| Heading font | Playfair Display (serif) |
| Body font | Inter (sans-serif) |
| Accent color | None |

### Notable UI Features

**3D product card hover flip**
```css
.card { perspective: 1000px; }
.card-inner { transform-style: preserve-3d; transition: transform .7s cubic-bezier(.4,0,.2,1); }
.card:hover .card-inner { transform: rotateY(180deg); }
.card-front, .card-back { backface-visibility: hidden; }
```

**DE / EN language toggle**
- Stored in `localStorage`
- Switches: welcome message, chips, placeholder text, modal text, product card labels
- Sends `lang: "de"` or `lang: "en"` with every `/chat` request
- Voice recognition language: `de-DE` or `en-US`

**Voice input**
- Uses `SpeechRecognition` API
- Language tracks the UI toggle (`de-DE` / `en-US`)

**Image upload modal (contact gate)**
- Fields: `name`, `email` (regex validated), `phone`
- File preview rendered before submission
- Submits via `FormData` multipart POST to `/search-by-image`

**Scroll behavior**
```javascript
// Correct — scrolls to the new turn, not past the product cards:
element.scrollIntoView({ behavior: 'smooth', block: 'start' });

// NOT this — causes scroll-to-bottom-of-products bug:
// container.scrollTop = container.scrollHeight;
```

---

## Local Setup

### Prerequisites

- Python 3.11+
- AWS account with Bedrock access in `us-east-1`
- Bedrock models enabled: `amazon.titan-embed-text-v2:0`, `amazon.titan-embed-image-v1`, `amazon.nova-pro-v1:0`
- Docker (for Lambda deployment only)

### Install

```powershell
# Clone
git clone https://github.com/ImranRafique847/Branded-show-shopping-assistence
cd tretter-shopping-assistant

# Virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Dependencies
pip install -r requirements.txt

# Environment
copy .env.example .env
# Edit .env and fill in your AWS credentials
```

### DynamoDB Tables (create once)

```bash
aws dynamodb create-table \
  --table-name tretter-chat-history \
  --attribute-definitions AttributeName=session_id,AttributeType=S AttributeName=timestamp,AttributeType=N \
  --key-schema AttributeName=session_id,KeyType=HASH AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST

aws dynamodb update-time-to-live \
  --table-name tretter-chat-history \
  --time-to-live-specification Enabled=true,AttributeName=ttl

aws dynamodb create-table \
  --table-name tretter-leads \
  --attribute-definitions AttributeName=lead_id,AttributeType=S AttributeName=timestamp,AttributeType=N \
  --key-schema AttributeName=lead_id,KeyType=HASH AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
```

---

## Building the Indexes

Run once. Each script is crash-safe and resumable via its `*_cache.jsonl` file.

```powershell
# 1. Scrape tretter.com (skip if you already have tretter_products_raw.jsonl)
python tretter_scraper.py

# 2. Translate DE → EN
python translate.py

# 3. Build product chunks
python build_chunks.py

# 4. Build text FAISS index (~7,476 Titan Text V2 API calls)
python build_text_index.py

# 5. Build image FAISS index (~7,476 Titan Multimodal API calls)
python build_image_index.py
```

**Expected outputs after all steps:**

```
product_chunks.json
text_index.faiss
text_metadata.json
image_index.faiss
image_metadata.json
```

---

## Running Locally

```powershell
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000

The `/health` endpoint reports index load status and DynamoDB connectivity:

```json
{
  "text_index": "loaded",
  "image_index": "loaded",
  "chat_history_table": "ok",
  "leads_table": "ok"
}
```

---

## Deployment Guide

### Overview

```
Docker image (python:3.11 Lambda base)
    │
    ▼  docker build --provenance=false
    │
    ▼  ECR push
    │  876493682275.dkr.ecr.us-east-1.amazonaws.com/ai-shopping-assistant:tretter-latest
    │
    ▼  Lambda: tretter-shopping-assistant
    │  3008 MB | 120 s timeout | Function URL (AuthType=NONE)
    │
    ▼  CloudFront: E104RJTSTWBCNC
       https://d31qqwhgzn5qcm.cloudfront.net
```

### Dockerfile Notes

- **Base image:** `public.ecr.aws/lambda/python:3.11`
- **`faiss-cpu==1.7.4`** must be installed **before** `requirements_lambda.txt` — the Lambda base image needs `gcc` available, and the pre-built faiss binary must be present before other packages are layered on top.
- **`--provenance=false`** is **required** on `docker build`. Without it, Docker BuildKit produces an OCI manifest list (index), which Lambda's ECR image loader rejects. The flag forces a Docker V2 manifest.
- **`pillow-avif-plugin`** is excluded from `requirements_lambda.txt` — it is not available in the Lambda image. AVIF/HEIC conversion works locally only; on Lambda, Pillow handles JPG/PNG/WEBP natively.

```dockerfile
# Example install order in Dockerfile
RUN pip install faiss-cpu==1.7.4
COPY requirements_lambda.txt .
RUN pip install -r requirements_lambda.txt
```

### Lambda Resource Policy (October 2025 Change)

Since October 2025, Lambda Function URLs require **two separate resource policy statements**:

```bash
# Statement 1: allow invoking via Function URL
aws lambda add-permission \
  --function-name tretter-shopping-assistant \
  --statement-id AllowFunctionURL \
  --action lambda:InvokeFunctionUrl \
  --principal "*" \
  --function-url-auth-type NONE

# Statement 2: allow invoke with condition
aws lambda add-permission \
  --function-name tretter-shopping-assistant \
  --statement-id AllowInvokeViaFunctionURL \
  --action lambda:InvokeFunction \
  --principal "*" \
  --condition '{ "StringEquals": { "lambda:InvokedViaFunctionUrl": "true" } }'
```

Using only one statement results in a 403 when calling the Function URL.

### CloudFront Configuration

| Setting | Value |
|---|---|
| Distribution ID | `E104RJTSTWBCNC` |
| Cache policy | CachingDisabled |
| Origin request policy | AllViewerExceptHostHeader |
| Allowed HTTP methods | GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE |
| Live URL | https://d31qqwhgzn5qcm.cloudfront.net |

### Automated Deployment

```powershell
# Full deploy: ECR login → docker build → push → Lambda create/update → Function URL → permissions
python deploy_lambda.py

# Create or reuse CloudFront distribution
python create_cloudfront.py
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values. These are also set as Lambda environment variables.

| Variable | Example / Default | Required | Description |
|---|---|---|---|
| `AWS_ACCESS_KEY_ID` | `AKIA...` | Yes | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | `...` | Yes | AWS credentials |
| `AWS_REGION` | `us-east-1` | Yes | Bedrock + DynamoDB region |
| `EMBEDDING_MODEL_ID` | `amazon.titan-embed-text-v2:0` | Yes | Titan Text V2 model ID |
| `IMAGE_EMBEDDING_MODEL_ID` | `amazon.titan-embed-image-v1` | Yes | Titan Multimodal model ID |
| `CHAT_MODEL_ID` | `amazon.nova-pro-v1:0` | Yes | Nova Pro model ID |
| `DYNAMODB_TABLE` | `tretter-chat-history` | Yes | Chat history table name |
| `LEADS_TABLE` | `tretter-leads` | Yes | Leads table name |
| `GITHUB_TOKEN` | `ghp_...` | Scripts only | GitHub PAT (repo scope) |
| `GITHUB_REPO` | `ImranRafique847/Branded-show-shopping-assistence` | Scripts only | Target GitHub repository |

---

## Utility Scripts

| Script | Purpose |
|---|---|
| `deploy_lambda.py` | Full deployment: ECR login, Docker build (`--provenance=false`), push, Lambda create/update, Function URL, public permissions |
| `create_cloudfront.py` | Creates or reuses a CloudFront distribution; reads credentials from `.env` via `python-dotenv` |
| `push_to_github.py` | Reads `GITHUB_TOKEN` from `.env`, sets the remote URL with the token embedded, runs `git push` |

---

## Known Issues & Decisions

### Lambda Function URL — Two Resource Policy Statements Required (October 2025)

AWS silently changed Lambda Function URL behavior in October 2025. A Function URL now requires **both** `lambda:InvokeFunctionUrl` and `lambda:InvokeFunction` (with the `lambda:InvokedViaFunctionUrl` condition) in the resource policy. Having only the traditional `InvokeFunctionUrl` statement returns HTTP 403. `deploy_lambda.py` adds both statements.

### Docker Build — `--provenance=false`

Docker BuildKit ≥ 0.11 defaults to producing an OCI image index (manifest list). Lambda's ECR image loader only accepts Docker V2 Schema 2 manifests. The `--provenance=false` flag on `docker build` suppresses the attestation manifest, producing the correct format.

### faiss-cpu Install Order

`faiss-cpu==1.7.4` uses a pre-built binary that links against libraries present in the Lambda base image at build time. Installing it **before** `requirements_lambda.txt` ensures the binary is resolved correctly. Installing it after other packages can cause import errors at Lambda startup.

### AVIF / HEIC Support — Local Only

`pillow-avif-plugin` is excluded from `requirements_lambda.txt` because the native library (`libavif`) is not present in the Lambda base image. On Lambda, the image upload endpoint accepts JPG, PNG, and WEBP. Locally, with `pillow-avif-plugin` installed, AVIF and HEIC files are auto-converted to JPEG before embedding.

### Init Phase Timeout (10 s Solved by Lazy Loading)

Lambda's init phase has a hard 10-second limit. Loading `text_index.faiss` + `image_index.faiss` + `product_chunks.json` at module import time took ~12 seconds and triggered init timeouts on cold starts. Solution: indexes are loaded inside the first request handler call. Cold start now takes ~4 seconds for index loading within the 120 s function timeout — well within the limit.

### Product Name Translation Suppressed

During translation pipeline development, Nova Pro was given bare model codes like `"Dublin 2.0"` or `"Arch-E"` and hallucinated full marketing paragraphs as "translations". Fix: `name_en = name` — product names are copied verbatim from the German source and never sent to the LLM.

### Scroll Bug — `scrollTop = scrollHeight` vs `scrollIntoView`

Using `container.scrollTop = container.scrollHeight` after a new chat turn scrolled past the assistant's text to the bottom of the product card grid. Fixed by using `element.scrollIntoView({ behavior: 'smooth', block: 'start' })` on the new turn element, which scrolls to the start of the turn rather than the absolute bottom of the DOM.

---

## Repository

- **GitHub:** https://github.com/ImranRafique847/Branded-show-shopping-assistence
- **Branch:** `main`
- **Live URL:** https://d31qqwhgzn5qcm.cloudfront.net

---

*Built with Amazon Bedrock (Nova Pro + Titan Embeddings), FastAPI, FAISS, and deployed on AWS Lambda + CloudFront.*
