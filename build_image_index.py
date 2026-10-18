#!/usr/bin/env python3
"""
build_image_index.py — Step 3 of the Tretter hybrid-RAG pipeline (MODE 2).

Embeds each product's IMAGE with Amazon Titan Multimodal Embeddings
(amazon.titan-embed-image-v1, 1024-dim) and builds a FAISS index for
"search by photo". The SAME model embeds an uploaded photo at query time, so
query image and product images live in one vector space.

Input : product_chunks.json  (+ the ../images/ files)
Output: image_index.faiss
        image_metadata.json   (per-vector product metadata, same order)

Crash-safe: cached to image_embeddings_cache.jsonl; re-run resumes.
Products whose image file is missing/unreadable are skipped (and logged).
"""

import base64
import json
import os
import time

import boto3
import numpy as np
import faiss
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
IMAGE_MODEL = os.getenv("IMAGE_EMBEDDING_MODEL_ID", "amazon.titan-embed-image-v1")
DIM = 1024

CHUNKS = "product_chunks.json"
IMAGES_ROOT = ".."          # local_image paths are relative to the project root
CACHE = "image_embeddings_cache.jsonl"
OUT_INDEX = "image_index.faiss"
OUT_META = "image_metadata.json"

bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)


def embed_image_b64(img_b64):
    body = json.dumps({
        "inputImage": img_b64,
        "embeddingConfig": {"outputEmbeddingLength": DIM},
    })
    for attempt in range(5):
        try:
            r = bedrock.invoke_model(
                modelId=IMAGE_MODEL, body=body,
                contentType="application/json", accept="application/json",
            )
            return json.loads(r["body"].read())["embedding"]
        except Exception as exc:  # noqa: BLE001
            if attempt == 4:
                raise
            time.sleep(2 * (attempt + 1))


def load_cache():
    done = {}
    if os.path.exists(CACHE):
        with open(CACHE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    done[rec["product_id"]] = rec["embedding"]
                except (json.JSONDecodeError, KeyError):
                    continue
    return done


def main():
    with open(CHUNKS, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    cache = load_cache()
    print(f"{len(chunks)} chunks; {len(cache)} already embedded (resume).")

    missing = 0
    cache_f = open(CACHE, "a", encoding="utf-8")
    for i, c in enumerate(chunks, 1):
        pid = c["product_id"]
        if pid in cache:
            continue
        rel = c["metadata"].get("local_image", "")
        path = os.path.join(IMAGES_ROOT, rel) if rel else ""
        if not path or not os.path.exists(path):
            missing += 1
            continue
        try:
            with open(path, "rb") as imgf:
                img_b64 = base64.b64encode(imgf.read()).decode("utf-8")
            emb = embed_image_b64(img_b64)
        except Exception as exc:  # noqa: BLE001
            print(f"  [skip] {pid}: {exc}")
            missing += 1
            continue
        cache[pid] = emb
        cache_f.write(json.dumps({"product_id": pid, "embedding": emb}) + "\n")
        if i % 100 == 0:
            cache_f.flush()
            print(f"  [{i}/{len(chunks)}] embedded (missing so far: {missing})")
    cache_f.close()

    vectors = []
    metadata = []
    for c in chunks:
        emb = cache.get(c["product_id"])
        if emb is None:
            continue
        vectors.append(emb)
        metadata.append(c["metadata"])

    mat = np.array(vectors, dtype=np.float32)
    # Titan multimodal vectors are not L2-normalized; normalize for cosine.
    faiss.normalize_L2(mat)
    index = faiss.IndexFlatIP(DIM)
    index.add(mat)
    faiss.write_index(index, OUT_INDEX)

    with open(OUT_META, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False)

    print(f"\nImage index built: {index.ntotal} vectors -> {OUT_INDEX}")
    print(f"Metadata: {OUT_META}  (images missing/skipped: {missing})")


if __name__ == "__main__":
    main()
