#!/usr/bin/env python3
"""
build_chunks.py — Step 1 of the Tretter hybrid-RAG pipeline.

Turns the scraped + translated product data into ONE self-contained chunk per
product. Each chunk carries:
  * product_id   — stable unique key (SKU, or a hash of the URL if SKU missing)
  * text         — English embedding text (all key fields in one block)
  * text_de      — German embedding text
  * metadata     — structured fields for display + hard filtering (price,
                   category, availability, image path, etc.)

The SAME chunk feeds both indexes later:
  * text   -> Titan Text V2            (Mode 1: text search)
  * image  -> Titan Multimodal (image) (Mode 2: search-by-photo)
bound together by product_id.

Input : ../tretter_products_en.json
Output: product_chunks.json   (list of chunks, one per product)
"""

import hashlib
import json
import os

SRC = os.path.join("..", "tretter_products_en.json")
OUT = "product_chunks.json"


def product_id_for(p):
    """Stable unique id: prefer SKU, else a short hash of the product URL."""
    sku = (p.get("sku") or "").strip()
    if sku:
        return sku
    url = (p.get("url") or "").strip()
    return "u_" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


def norm_image(path):
    """Normalise the local image path to forward slashes (cross-platform)."""
    return (path or "").replace("\\", "/")


def build_text(p, lang):
    """Build the single-block embedding text for one product."""
    if lang == "en":
        name = p.get("name_en") or p.get("name") or ""
        gender = p.get("gender_en") or p.get("gender") or ""
        category = p.get("category_path_en") or p.get("category_en") or p.get("category") or ""
        desc = p.get("description_en") or p.get("description") or ""
    else:
        name = p.get("name") or ""
        gender = p.get("gender") or ""
        category = p.get("category_path") or p.get("category") or ""
        desc = p.get("description") or ""

    brand = p.get("brand") or ""
    price = p.get("price")
    currency = p.get("currency") or "EUR"
    avail = p.get("availability") or ""

    parts = []
    if name:
        parts.append(f"Product: {name}")
    if brand:
        parts.append(f"Brand: {brand}")
    if category:
        parts.append(f"Category: {category}")
    if gender:
        parts.append(f"Gender: {gender}")
    if price not in (None, ""):
        parts.append(f"Price: {price} {currency}")
    if avail:
        parts.append(f"Availability: {avail}")
    header = " | ".join(parts)
    return (header + ". " + desc).strip()


def main():
    if not os.path.exists(SRC):
        raise SystemExit(f"Source not found: {SRC}")

    with open(SRC, "r", encoding="utf-8") as f:
        products = json.load(f)

    chunks = []
    seen_ids = {}
    for p in products:
        pid = product_id_for(p)
        # Guarantee uniqueness even if two products share a SKU.
        if pid in seen_ids:
            seen_ids[pid] += 1
            pid = f"{pid}__{seen_ids[pid]}"
        else:
            seen_ids[pid] = 0

        # Price as float when possible (for hard numeric filtering later).
        price_val = None
        try:
            price_val = float(p.get("price"))
        except (TypeError, ValueError):
            price_val = None

        chunk = {
            "product_id": pid,
            "text": build_text(p, "en"),
            "text_de": build_text(p, "de"),
            "metadata": {
                "product_id": pid,
                "name": p.get("name_en") or p.get("name") or "",
                "name_de": p.get("name") or "",
                "brand": p.get("brand") or "",
                "price": price_val if price_val is not None else "",
                "currency": p.get("currency") or "EUR",
                "old_price": p.get("old_price") or "",
                "availability": p.get("availability") or "",
                "condition": p.get("condition") or "",
                "gender": p.get("gender_en") or p.get("gender") or "",
                "category": p.get("category_en") or p.get("category") or "",
                "category_path": p.get("category_path_en") or p.get("category_path") or "",
                "category_de": p.get("category") or "",
                "sku": p.get("sku") or "",
                "url": p.get("url") or "",
                "image": p.get("image") or "",
                "local_image": norm_image(p.get("local_image")),
                "description": p.get("description_en") or p.get("description") or "",
            },
        }
        chunks.append(chunk)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    # Quick stats.
    with_img = sum(1 for c in chunks if c["metadata"]["local_image"]
                   and os.path.exists(os.path.join("..", c["metadata"]["local_image"])))
    print(f"Built {len(chunks)} product chunks -> {OUT}")
    print(f"Chunks whose local image file exists: {with_img}")
    print(f"Unique product_ids: {len(set(c['product_id'] for c in chunks))}")


if __name__ == "__main__":
    main()
