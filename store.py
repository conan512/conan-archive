# -*- coding: utf-8 -*-
"""Sharded archive storage.

The full archive is ~26MB, above GitHub's 25MB web-upload limit, so it is kept
as data/posts/NN.json shards (~3.5MB each) plus data/meta.json.

A legacy single-file data/posts.json is still read if present, so nothing breaks.
"""
import json, os, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(ROOT, "data")
SHARD_DIR = os.path.join(DIR, "posts")
LEGACY = os.path.join(DIR, "posts.json")
META = os.path.join(DIR, "meta.json")
BUCKET = 2000          # posts per shard, by post id


def _w(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)


def load():
    """-> (meta: dict, posts: dict[int, post], updated: str)"""
    posts, meta, updated = {}, {}, ""

    if os.path.isdir(SHARD_DIR):
        for f in sorted(glob.glob(os.path.join(SHARD_DIR, "*.json"))):
            try:
                for p in json.load(open(f, encoding="utf-8")):
                    posts[p["id"]] = p
            except Exception as e:
                print(f"  ! bad shard {os.path.basename(f)}: {e}")
        if os.path.exists(META):
            try:
                m = json.load(open(META, encoding="utf-8"))
                meta, updated = m.get("meta", {}), m.get("updated", "")
            except Exception:
                pass

    if not posts and os.path.exists(LEGACY):
        try:
            d = json.load(open(LEGACY, encoding="utf-8"))
            for p in d.get("posts", []):
                posts[p["id"]] = p
            meta, updated = d.get("meta", {}), d.get("updated", "")
            print(f"  (loaded legacy posts.json: {len(posts)} posts)")
        except Exception as e:
            print(f"  ! legacy load failed: {e}")

    return meta, posts, updated


def save(meta, posts, updated):
    """posts: dict[int, post] or list. Writes shards + meta, prunes stale shards."""
    if isinstance(posts, dict):
        posts = list(posts.values())
    posts.sort(key=lambda x: -x["id"])

    buckets = {}
    for p in posts:
        buckets.setdefault(p["id"] // BUCKET, []).append(p)

    os.makedirs(SHARD_DIR, exist_ok=True)
    keep = set()
    for b, items in buckets.items():
        name = f"{b:02d}.json"
        keep.add(name)
        _w(os.path.join(SHARD_DIR, name), sorted(items, key=lambda x: -x["id"]))

    for f in glob.glob(os.path.join(SHARD_DIR, "*.json")):
        if os.path.basename(f) not in keep:
            os.remove(f)

    _w(META, {"meta": meta, "updated": updated, "count": len(posts),
              "shards": sorted(keep), "bucket": BUCKET})
    return len(posts), len(keep)
