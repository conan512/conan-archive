#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download Telegram CDN images locally and convert them to WebP.

Creates media/<shard>/<hash>.webp and media/manifest.json mapping
original CDN url -> local relative path. Fully incremental & resumable:
already-downloaded images and previously-failed (404) urls are skipped.
"""
import concurrent.futures as cf
import hashlib, io, json, os, sys, threading, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "posts.json")
MEDIA = os.path.join(ROOT, "media")
MANIFEST = os.path.join(MEDIA, "manifest.json")

MAX_W = int(os.environ.get("MAX_W", "1280"))
QUALITY = int(os.environ.get("QUALITY", "80"))
WORKERS = int(os.environ.get("WORKERS", "16"))
LIMIT = int(os.environ.get("LIMIT", "0"))          # 0 = no limit
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36"}

from PIL import Image
Image.MAX_IMAGE_PIXELS = None

lock = threading.Lock()
state = {"ok": 0, "skip": 0, "fail": 0, "bytes": 0}


def key(url):
    return hashlib.sha1(url.encode()).hexdigest()[:16]


def collect(posts):
    """All image urls referenced by the archive, newest posts first."""
    urls = []
    seen = set()
    for p in posts:
        cand = list(p.get("photos") or [])
        for v in p.get("videos") or []:
            if v.get("thumb"):
                cand.append(v["thumb"])
        if p.get("link") and p["link"].get("image"):
            cand.append(p["link"]["image"])
        if p.get("sticker"):
            cand.append(p["sticker"])
        for u in cand:
            if u and u.startswith("http") and u not in seen:
                seen.add(u)
                urls.append(u)
    return urls


def fetch(url, man, failed):
    k = key(url)
    if k in man:
        with lock:
            state["skip"] += 1
        return
    if k in failed:
        with lock:
            state["skip"] += 1
        return
    rel = f"{k[:2]}/{k}.webp"
    dst = os.path.join(MEDIA, rel)
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        with lock:
            man[k] = rel
            state["skip"] += 1
        return
    try:
        req = urllib.request.Request(url, headers=UA)
        raw = urllib.request.urlopen(req, timeout=40).read()
        im = Image.open(io.BytesIO(raw))
        im.load()
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGBA", im.size, (10, 13, 22, 255))
            im = Image.alpha_composite(bg, im).convert("RGB")
        else:
            im = im.convert("RGB")
        if max(im.size) > MAX_W:
            im.thumbnail((MAX_W, MAX_W), Image.LANCZOS)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        tmp = dst + ".tmp"
        im.save(tmp, "WEBP", quality=QUALITY, method=4)
        os.replace(tmp, dst)
        with lock:
            man[k] = rel
            state["ok"] += 1
            state["bytes"] += os.path.getsize(dst)
    except urllib.error.HTTPError as e:
        with lock:
            state["fail"] += 1
            if e.code in (403, 404, 410):
                failed.add(k)
    except Exception:
        with lock:
            state["fail"] += 1


def save(man, failed):
    os.makedirs(MEDIA, exist_ok=True)
    tmp = MANIFEST + ".tmp"
    json.dump({"map": man, "failed": sorted(failed)},
              open(tmp, "w", encoding="utf-8"), separators=(",", ":"))
    os.replace(tmp, MANIFEST)


def main():
    posts = json.load(open(DATA, encoding="utf-8"))["posts"]
    urls = collect(posts)
    if LIMIT:
        urls = urls[:LIMIT]

    man, failed = {}, set()
    if os.path.exists(MANIFEST):
        try:
            old = json.load(open(MANIFEST, encoding="utf-8"))
            man = old.get("map", {})
            failed = set(old.get("failed", []))
            print(f"loaded manifest: {len(man)} cached, {len(failed)} known-dead")
        except Exception:
            pass

    todo = [u for u in urls if key(u) not in man and key(u) not in failed]
    print(f"{len(urls)} total urls · {len(todo)} to download · {WORKERS} workers")
    t0 = time.time()
    done = 0
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(fetch, u, man, failed) for u in todo]
        for _ in cf.as_completed(futs):
            done += 1
            if done % 250 == 0:
                el = time.time() - t0
                rate = done / el if el else 0
                eta = (len(todo) - done) / rate / 60 if rate else 0
                print(f"  {done}/{len(todo)} ok={state['ok']} fail={state['fail']} "
                      f"{state['bytes']/1e6:.0f}MB {rate:.1f}/s eta={eta:.0f}min", flush=True)
                with lock:
                    save(man, failed)
    save(man, failed)
    print(f"✓ done: {state['ok']} downloaded, {state['skip']} cached, {state['fail']} failed, "
          f"{state['bytes']/1e6:.0f}MB in {(time.time()-t0)/60:.1f}min")
    print(f"  manifest: {len(man)} images -> {MANIFEST}")


if __name__ == "__main__":
    main()
