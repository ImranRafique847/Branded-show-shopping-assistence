#!/usr/bin/env python3
"""
main.py — FastAPI backend for the TRETTER hybrid-RAG shopping assistant.

Two always-on modes:

  MODE 1 — Text search (Corrective RAG)
    User types a query -> LLM rewrites it -> Titan Text embedding ->
    text_index (FAISS) -> HARD FILTERS (price / category / in-stock) ->
    LLM writes a short honest reply. Vectors only RANK; price & category are
    enforced by filters, never by the embedding.

  MODE 2 — Search by photo  (lead-gated)
    User uploads a shoe photo -> MUST provide name/email/phone first ->
    Titan Multimodal embeds the photo -> image_index (FAISS) ->
    filtered to IN-STOCK -> returns visually similar products.
    The lead (name/email/phone + query) is saved to DynamoDB.

Indexes + metadata are produced by build_text_index.py / build_image_index.py.
They are loaded from local files by default, or from S3 if S3_* env vars are set.
"""

import base64
import json
import os
import re
import time
import uuid
import tempfile

import boto3
import faiss
import numpy as np
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

AWS_REGION   = os.getenv("AWS_REGION", "us-east-1")
TEXT_MODEL   = os.getenv("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
IMAGE_MODEL  = os.getenv("IMAGE_EMBEDDING_MODEL_ID", "amazon.titan-embed-image-v1")
CHAT_MODEL   = os.getenv("CHAT_MODEL_ID", "amazon.nova-pro-v1:0")
DIM          = 1024
TOP_K        = 12

# Local index files (produced by the build scripts).
TEXT_INDEX   = os.getenv("TEXT_INDEX", "text_index.faiss")
TEXT_META    = os.getenv("TEXT_META", "text_metadata.json")
IMAGE_INDEX  = os.getenv("IMAGE_INDEX", "image_index.faiss")
IMAGE_META   = os.getenv("IMAGE_META", "image_metadata.json")

# DynamoDB tables (live).
CHAT_TABLE_NAME = os.getenv("DYNAMODB_TABLE", "tretter-chat-history")
LEADS_TABLE_NAME = os.getenv("LEADS_TABLE", "tretter-leads")

app = FastAPI(title="TRETTER Shopping Assistant")

bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

try:
    chat_table = dynamodb.Table(CHAT_TABLE_NAME)
    chat_table.load()
    print(f"[ok] DynamoDB chat table: {CHAT_TABLE_NAME}")
except Exception as e:  # noqa: BLE001
    print(f"[warn] chat table unavailable: {e}")
    chat_table = None

try:
    leads_table = dynamodb.Table(LEADS_TABLE_NAME)
    leads_table.load()
    print(f"[ok] DynamoDB leads table: {LEADS_TABLE_NAME}")
except Exception as e:  # noqa: BLE001
    print(f"[warn] leads table unavailable: {e}")
    leads_table = None


# ── Load FAISS indexes ─────────────────────────────────────────

def _load_index(path):
    return faiss.read_index(path)

# Lazy-loaded indexes — loaded on first request, not at module init.
# Keeps Lambda cold-start init under 10s (avoids init phase timeout).
text_index     = None
text_metadata  = None
image_index    = None
image_metadata = None


def _ensure_indexes():
    """Load FAISS indexes on first use."""
    global text_index, text_metadata, image_index, image_metadata
    if text_index is not None:
        return
    print("Loading indexes (lazy)...")
    text_index = _load_index(TEXT_INDEX)
    with open(TEXT_META, "r", encoding="utf-8") as f:
        text_metadata = json.load(f)
    print(f"[ok] text index: {text_index.ntotal} vectors")
    image_index = _load_index(IMAGE_INDEX)
    with open(IMAGE_META, "r", encoding="utf-8") as f:
        image_metadata = json.load(f)
    print(f"[ok] image index: {image_index.ntotal} vectors")


# ── Embeddings ─────────────────────────────────────────────────

def embed_text(text):
    body = json.dumps({"inputText": text[:8000], "dimensions": DIM, "normalize": True})
    r = bedrock.invoke_model(modelId=TEXT_MODEL, body=body,
                             contentType="application/json", accept="application/json")
    return np.array(json.loads(r["body"].read())["embedding"], dtype=np.float32)


def normalize_image_to_jpeg_b64(raw_bytes):
    """
    Convert ANY uploaded image (AVIF, HEIC, PNG, WEBP, GIF, etc.) into a clean
    RGB JPEG that Amazon Titan Multimodal accepts, and return base64.
    Titan only supports PNG/JPEG/GIF/WEBP, so formats like AVIF must be converted.
    Also downscales very large images to keep the Bedrock payload small.
    """
    from io import BytesIO
    from PIL import Image

    try:
        import pillow_avif  # noqa: F401  (registers AVIF support if installed)
    except Exception:
        pass

    img = Image.open(BytesIO(raw_bytes))
    img = img.convert("RGB")                      # drop alpha / palette / CMYK
    img.thumbnail((1024, 1024))                   # cap dimensions
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def embed_image_b64(img_b64):
    body = json.dumps({"inputImage": img_b64,
                       "embeddingConfig": {"outputEmbeddingLength": DIM}})
    r = bedrock.invoke_model(modelId=IMAGE_MODEL, body=body,
                             contentType="application/json", accept="application/json")
    v = np.array(json.loads(r["body"].read())["embedding"], dtype=np.float32).reshape(1, -1)
    faiss.normalize_L2(v)   # match the index (which was L2-normalized)
    return v


# ── LLM (Nova) ─────────────────────────────────────────────────

def call_llm(prompt, system=""):
    body_dict = {
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"maxTokens": 600, "temperature": 0.5},
    }
    if system:
        body_dict["system"] = [{"text": system}]
    r = bedrock.invoke_model(modelId=CHAT_MODEL, body=json.dumps(body_dict),
                             contentType="application/json", accept="application/json")
    return json.loads(r["body"].read())["output"]["message"]["content"][0]["text"].strip()


# ── DynamoDB helpers ───────────────────────────────────────────

def save_message(session_id, role, content):
    if not chat_table:
        return
    try:
        chat_table.put_item(Item={
            "session_id": session_id,
            "timestamp": int(time.time() * 1000),
            "role": role, "content": content,
            "ttl": int(time.time()) + 7 * 24 * 3600,
        })
    except Exception as e:  # noqa: BLE001
        print(f"[dynamo] save_message: {e}")


def load_history(session_id, limit=20):
    if not chat_table:
        return []
    try:
        from boto3.dynamodb.conditions import Key
        resp = chat_table.query(
            KeyConditionExpression=Key("session_id").eq(session_id),
            ScanIndexForward=True, Limit=limit)
        items = resp.get("Items", [])[-limit:]
        return [{"role": i["role"], "content": i["content"]} for i in items]
    except Exception as e:  # noqa: BLE001
        print(f"[dynamo] load_history: {e}")
        return []


def save_lead(name, email, phone, query, matched_ids, session_id):
    if not leads_table:
        print(f"[lead-not-saved] {name} {email} {phone}")
        return False
    try:
        leads_table.put_item(Item={
            "lead_id": str(uuid.uuid4()),
            "timestamp": int(time.time() * 1000),
            "name": name, "email": email, "phone": phone,
            "query": query or "image-search",
            "matched_product_ids": matched_ids[:10],
            "session_id": session_id or "",
        })
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[dynamo] save_lead: {e}")
        return False


# ── Hard filters (price / category / stock) applied AFTER retrieval ──

CATEGORY_KEYWORDS = {
    "sneaker": ["sneaker"],
    "boot": ["boot", "stiefel"],
    "sandal": ["sandal", "open shoes", "offene", "pantolette"],
    "slipper": ["slipper", "hausschuh", "mokassin", "loafer"],
    "sports": ["sport", "running", "hiking", "wander", "lauf", "fitness"],
    "business": ["business", "lace-up", "schnür", "elegant"],
}


def parse_filters(text):
    t = text.lower()
    f = {"max_price": None, "min_price": None, "category": None, "in_stock": False}

    m = re.search(r"(?:under|below|less than|unter|bis zu|max)\s*€?\$?\s*(\d+(?:[.,]\d+)?)", t)
    if m:
        f["max_price"] = float(m.group(1).replace(",", "."))
    m = re.search(r"(?:over|above|more than|über|ab)\s*€?\$?\s*(\d+(?:[.,]\d+)?)", t)
    if m:
        f["min_price"] = float(m.group(1).replace(",", "."))

    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(k in t for k in kws):
            f["category"] = kws
            break

    if any(w in t for w in ["in stock", "available", "verfügbar", "auf lager"]):
        f["in_stock"] = True
    return f


def passes_filters(item, f, force_in_stock=False):
    # Price
    price = item.get("price")
    if isinstance(price, (int, float)):
        if f["max_price"] is not None and price > f["max_price"]:
            return False
        if f["min_price"] is not None and price < f["min_price"]:
            return False
    # Category — check against category/category_path/name
    if f["category"]:
        hay = (str(item.get("category", "")) + " " +
               str(item.get("category_path", "")) + " " +
               str(item.get("name", ""))).lower()
        if not any(k in hay for k in f["category"]):
            return False
    # Stock
    if (f["in_stock"] or force_in_stock):
        if "instock" not in str(item.get("availability", "")).lower():
            return False
    return True


# ── Retrieval ──────────────────────────────────────────────────

def search_text(query, original="", k=TOP_K):
    _ensure_indexes()
    f = parse_filters(query + " " + original)
    emb = embed_text(query).reshape(1, -1)
    scores, idxs = text_index.search(emb, k * 8)
    out, seen = [], set()
    for s, i in zip(scores[0], idxs[0]):
        if i == -1:
            continue
        item = dict(text_metadata[i])
        if not passes_filters(item, f):
            continue
        pid = item.get("product_id")
        if pid in seen:
            continue
        seen.add(pid)
        item["score"] = float(s)
        out.append(item)
        if len(out) >= k:
            break
    return out


def search_image(img_b64, k=TOP_K):
    _ensure_indexes()
    emb = embed_image_b64(img_b64)
    scores, idxs = image_index.search(emb, k * 8)
    out, seen = [], set()
    f = {"max_price": None, "min_price": None, "category": None, "in_stock": True}
    for s, i in zip(scores[0], idxs[0]):
        if i == -1:
            continue
        item = dict(image_metadata[i])
        # Mode 2 is for out-of-stock alternatives -> only show buyable items.
        if not passes_filters(item, f, force_in_stock=True):
            continue
        pid = item.get("product_id")
        if pid in seen:
            continue
        seen.add(pid)
        item["score"] = float(s)
        out.append(item)
        if len(out) >= k:
            break
    return out


# ── CRAG text pipeline ─────────────────────────────────────────

def rewrite_query(msg, history):
    """CRAG Step 1 — rewrite the shopper's message into a precise search query."""
    hist = "\n".join(f"{t['role'].upper()}: {t['content']}" for t in history[-6:]) if history else "No previous conversation"
    prompt = f"""You are an expert search query optimizer for the TRETTER shoe store.

Your task: Rewrite the user's message into the most effective search query to retrieve relevant shoe products.

Rules:
1. Extract ALL relevant attributes: shoe type, gender (men/women/kids), age group, color, material, brand, size, price range
2. Fix spelling mistakes and expand abbreviations
3. Use conversation history to understand follow-up questions (e.g. "show me cheaper ones" -> keep the previous shoe type)
4. Be specific - "women black leather ankle boots" is better than "boots"
5. Return ONLY the rewritten search query - no explanation, no punctuation at the end

Conversation history:
{hist}

User message: {msg}

Optimized search query:"""
    return call_llm(prompt).strip().strip('"').strip("'")


def detect_intent(msg):
    m = msg.lower().strip()
    greetings = {"hi", "hello", "hey", "thanks", "thank you", "bye", "ok", "okay",
                 "hallo", "hi!", "danke", "tschüss", "guten tag", "guten morgen",
                 "servus", "moin"}
    if m in greetings:
        return "conversation"
    # Help / capability / chit-chat phrases (EN + DE) -> conversation.
    chat_phrases = ["what can you do", "who are you", "how are you", "help me",
                    "was kannst du", "wer bist du", "wie geht", "was machst du",
                    "kannst du mir helfen", "hilf mir", "wie funktioniert"]
    if any(p in m for p in chat_phrases):
        return "conversation"
    words = m.split()
    kw = ["shoe", "schuh", "sneaker", "boot", "stiefel", "sandal", "slipper",
          "loafer", "heel", "pump", "find", "show", "buy", "need", "want",
          "men", "women", "kid", "herren", "damen", "kinder", "under", "price"]
    if len(words) <= 2 and not any(k in m for k in kw):
        return "conversation"
    return "search"


def generate_reply(original, products, lang="en"):
    """CRAG Step 3 — brief, honest reply based ONLY on products actually found."""
    lang_instruction = (
        "Antworte AUF DEUTSCH. Alle Texte, Zahlen und Einheiten auf Deutsch."
        if lang == "de" else
        "Reply in ENGLISH."
    )
    system = f"""You are a helpful AI shopping assistant for the TRETTER shoe store.
The user's search results are displayed as product cards on screen.
{lang_instruction}
Write a SHORT 2-3 sentence honest response following these STRICT rules:
1. Only mention attributes the USER explicitly asked for
2. Do NOT invent details like sizes, colors, materials, or styles the user did not ask for
3. Only mention a price range if the user asked for a specific budget
4. State how many products were found
5. Keep it friendly and under 3 sentences
6. Do NOT list individual products"""

    import re
    budget_mentioned = bool(re.search(r"€?\$?\d+|under|below|less than|unter|bis|budget|cheap|affordable|günstig", original.lower()))

    if not products:
        summary = "No products found matching this query."
    else:
        prices = [p["price"] for p in products if isinstance(p.get("price"), (int, float))]
        summary = f"{len(products)} products found."
        if prices:
            summary += f" Price range: €{min(prices):.2f} to €{max(prices):.2f}."

    prompt = f"""User asked: {original}
{summary}
User mentioned a budget: {budget_mentioned}

Write a short honest response. Only mention what the user asked for. Do not add details they did not request."""
    return call_llm(prompt, system)


def conversational_reply(msg, history, lang="en"):
    """Friendly conversational response when the user is just chatting."""
    lang_instruction = (
        "Antworte AUF DEUTSCH."
        if lang == "de" else
        "Reply in ENGLISH."
    )
    system = f"""You are a friendly AI shopping assistant for the TRETTER shoe store.
You help users find shoes and accessories for men, women and kids.
{lang_instruction}
When users greet you or chat casually, respond warmly and briefly.
Remind them they can find shoes by description, or upload a photo to find similar styles.
Keep responses under 3 sentences."""
    hist = "\n".join(f"{t['role'].upper()}: {t['content']}" for t in history[-4:]) if history else "None"
    return call_llm(f"Previous conversation:\n{hist}\n\nUser: {msg}\n\nRespond conversationally:", system)


# ── API models + routes ────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    lang: Optional[str] = "en"   # "de" or "en" — set by the UI language toggle


class ChatResponse(BaseModel):
    reply: str
    products: list
    rewritten_query: str
    session_id: str


@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse("static/index.html")


@app.get("/session")
async def new_session():
    return {"session_id": str(uuid.uuid4())}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "Message cannot be empty")
    session_id = req.session_id or str(uuid.uuid4())
    history = load_history(session_id)

    if detect_intent(req.message) == "conversation":
        reply = conversational_reply(req.message, history, req.lang or "en")
        save_message(session_id, "user", req.message)
        save_message(session_id, "assistant", reply)
        return ChatResponse(reply=reply, products=[], rewritten_query="", session_id=session_id)

    rewritten = rewrite_query(req.message, history)
    products = search_text(rewritten, req.message)
    reply = generate_reply(req.message, products, req.lang or "en")
    save_message(session_id, "user", req.message)
    save_message(session_id, "assistant", reply)
    return ChatResponse(reply=reply, products=products,
                        rewritten_query=rewritten, session_id=session_id)


@app.post("/search-by-image")
async def search_by_image(
    image: UploadFile = File(...),
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    session_id: str = Form(""),
):
    # Lead gate: name/email/phone are REQUIRED for image search.
    name, email, phone = name.strip(), email.strip(), phone.strip()
    if not name or not email or not phone:
        raise HTTPException(400, "Name, email and phone are required for image search.")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise HTTPException(400, "Please provide a valid email address.")

    raw = await image.read()
    if not raw:
        raise HTTPException(400, "Empty image upload.")

    # Convert whatever was uploaded (incl. AVIF/HEIC) to a Titan-friendly JPEG.
    try:
        img_b64 = normalize_image_to_jpeg_b64(raw)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"Could not read that image file. Try a JPG or PNG. ({e})")

    try:
        products = search_image(img_b64)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Image search failed: {e}")

    matched_ids = [p.get("product_id", "") for p in products]
    saved = save_lead(name, email, phone, "image-search", matched_ids, session_id)

    if products:
        reply = (f"Danke {name}! Hier sind {len(products)} verfügbare Schuhe, die deinem Foto ähneln. "
                 f"/ Here are {len(products)} in-stock shoes similar to your photo.")
    else:
        reply = (f"Danke {name}! Leider kein passender Treffer auf Lager — versuch ein anderes Foto. "
                 f"/ No close in-stock match — try another photo.")
    return {"reply": reply, "products": products, "lead_saved": saved,
            "session_id": session_id or str(uuid.uuid4())}


@app.get("/health")
async def health():
    _ensure_indexes()
    return {"status": "ok",
            "text_vectors": text_index.ntotal if text_index else 0,
            "image_vectors": image_index.ntotal if image_index else 0,
            "chat_table": bool(chat_table),
            "leads_table": bool(leads_table)}
