#!/usr/bin/env python3
"""
build_text_index.py — Step 2 of the Tretter hybrid-RAG pipeline (MODE 1).

Embeds each product chunk's English text with Amazon Titan Text Embeddings V2
(1024-dim) and builds a FAISS index for text search.

Input : product_chunks.json
Output: text_index.faiss        (FAISS index, inner-product / cosine)
        text_metadata.json      (per-vector product metadata, same order)

Crash-safe: embeddings are cached to text_embeddings_cache.jsonl as they are
produced, so a re-run resumes instantly without re-calling Bedrock.
"""

import json
import os
import time

import boto3
import numpy as np
import faiss
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
TEXT_MODEL = os.getenv("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
DIM = 1024

CHUNKS = "product_chunks.json"
CACHE = "text_embeddings_cache.jsonl"
OUT_INDEX = "text_index.faiss"
OUT_META = "text_metadata.json"

bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)


def embed_text(text):
    body = json.dumps({"inputText": text[:8000], "dimensions": DIM, "normalize": True})
    for attempt in range(5):
        try:
            r = bedrock.invoke_model(
                modelId=TEXT_MODEL, body=body,
                contentType="application/json", accept="application/json",
            )
            return json.loads(r["body"].read())["embedding"]
        except Exception as exc:  # noqa: BLE001 (throttling/transient)
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

    cache_f = open(CACHE, "a", encoding="utf-8")
    for i, c in enumerate(chunks, 1):
        pid = c["product_id"]
        if pid in cache:
            continue
        emb = embed_text(c["text"])
        cache[pid] = emb
        cache_f.write(json.dumps({"product_id": pid, "embedding": emb}) + "\n")
        if i % 100 == 0:
            cache_f.flush()
            print(f"  [{i}/{len(chunks)}] embedded")
    cache_f.close()

    # Build FAISS index in chunk order; metadata parallels the vectors.
    vectors = []
    metadata = []
    for c in chunks:
        emb = cache.get(c["product_id"])
        if emb is None:
            continue
        vectors.append(emb)
        metadata.append(c["metadata"])

    mat = np.array(vectors, dtype=np.float32)
    index = faiss.IndexFlatIP(DIM)   # inner product == cosine (vectors normalized)
    index.add(mat)
    faiss.write_index(index, OUT_INDEX)

    with open(OUT_META, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False)

    print(f"\nText index built: {index.ntotal} vectors -> {OUT_INDEX}")
    print(f"Metadata: {OUT_META}")


if __name__ == "__main__":
    main()
