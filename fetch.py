#!/usr/bin/env python3
"""Scrape public Telegram channel web preview (t.me/s/<channel>) into posts.json"""
import json, os, re, sys, time, urllib.request, urllib.error
from bs4 import BeautifulSoup

CHANNEL = os.environ.get("TG_CHANNEL", "DetectiveConanIR")
OUT = os.environ.get("OUT", os.path.join(os.path.dirname(__file__), "..", "data", "posts.json"))
MAX_PAGES = int(os.environ.get("MAX_PAGES", "40"))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36"


def get(url, tries=4):
    for i in range(tries):
        try:
            r = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "fa,en"})
            return urllib.request.urlopen(r, timeout=30).read().decode("utf-8", "replace")
        except Exception as e:
            if i == tries - 1:
                print("  ! fail", url, e, file=sys.stderr)
                return None
            time.sleep(2 * (i + 1))


def bg_url(style):
    m = re.search(r"url\('([^']+)'\)", style or "")
    return m.group(1) if m else None


def parse_post(m):
    pid = m.get("data-post") or ""
    num = int(pid.split("/")[-1]) if pid.split("/")[-1].isdigit() else 0
    t = m.select_one(".tgme_widget_message_text.js-message_text") or m.select_one(".tgme_widget_message_text")

    html = ""
    text = ""
    if t:
        for br in t.select("br"):
            br.replace_with("\n")
        text = t.get_text("", strip=False).strip()
        html = t.decode_contents()

    tags = re.findall(r"#([\w\u0600-\u06FF_]+)", text)
    seen, hashtags = set(), []
    for h in tags:
        if h.lower() not in seen:
            seen.add(h.lower())
            hashtags.append(h)

    photos = [bg_url(p.get("style")) for p in m.select(".tgme_widget_message_photo_wrap")]
    photos = [p for p in photos if p]

    videos = []
    for v in m.select("video.tgme_widget_message_video"):
        videos.append({"src": v.get("src"), "thumb": bg_url(
            (v.find_parent(class_="tgme_widget_message_video_wrap") or v).get("style"))})
    for rt in m.select(".tgme_widget_message_video_thumb"):
        u = bg_url(rt.get("style"))
        if u and not any(x.get("thumb") == u for x in videos):
            videos.append({"src": None, "thumb": u})

    docs = []
    for d in m.select(".tgme_widget_message_document"):
        name = d.select_one(".tgme_widget_message_document_title")
        size = d.select_one(".tgme_widget_message_document_extra")
        docs.append({"name": name.get_text(strip=True) if name else "file",
                     "size": size.get_text(strip=True) if size else ""})

    voice = bool(m.select(".tgme_widget_message_voice"))
    audio = None
    a = m.select_one(".tgme_widget_message_audio")
    if a:
        ti = m.select_one(".tgme_widget_message_audio_title")
        au = m.select_one(".tgme_widget_message_audio_author")
        audio = {"title": ti.get_text(strip=True) if ti else "",
                 "author": au.get_text(strip=True) if au else ""}

    poll = None
    p = m.select_one(".tgme_widget_message_poll")
    if p:
        q = p.select_one(".tgme_widget_message_poll_question")
        poll = {"question": q.get_text(strip=True) if q else "",
                "options": [o.get_text(" ", strip=True) for o in p.select(".tgme_widget_message_poll_option")]}

    link = None
    lp = m.select_one(".tgme_widget_message_link_preview")
    if lp:
        st = lp.select_one(".link_preview_site_name")
        lt = lp.select_one(".link_preview_title")
        ld = lp.select_one(".link_preview_description")
        li = lp.select_one(".link_preview_image")
        link = {"url": lp.get("href"),
                "site": st.get_text(strip=True) if st else "",
                "title": lt.get_text(strip=True) if lt else "",
                "desc": ld.get_text(" ", strip=True) if ld else "",
                "image": bg_url(li.get("style")) if li else None}

    sticker = None
    for s in m.select(".tgme_widget_message_sticker"):
        sticker = s.get("data-webp") or bg_url(s.get("style"))

    dt = m.select_one("time")
    views = m.select_one(".tgme_widget_message_views")
    fwd = m.select_one(".tgme_widget_message_forwarded_from_name")
    reply = m.select_one(".tgme_widget_message_reply")

    return {
        "id": num,
        "url": f"https://t.me/{CHANNEL}/{num}",
        "date": dt.get("datetime") if dt else None,
        "text": text,
        "html": html,
        "hashtags": hashtags,
        "photos": photos,
        "videos": videos,
        "docs": docs,
        "voice": voice,
        "audio": audio,
        "poll": poll,
        "link": link,
        "sticker": sticker,
        "views": views.get_text(strip=True) if views else "",
        "forwarded": fwd.get_text(strip=True) if fwd else None,
        "reply": reply.get_text(" ", strip=True)[:120] if reply else None,
    }


def save(path, meta, posts):
    out = {"meta": meta, "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "posts": sorted(posts.values(), key=lambda x: -x["id"])}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    json.dump(out, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, path)
    return len(out["posts"])


def main():
    posts = {}
    path = os.path.abspath(OUT)
    if os.path.exists(path):
        try:
            for p in json.load(open(path, encoding="utf-8")).get("posts", []):
                posts[p["id"]] = p
            print(f"loaded {len(posts)} existing posts")
        except Exception:
            pass

    meta = {}
    before = int(os.environ["START_BEFORE"]) if os.environ.get("START_BEFORE") else None
    if before is None and posts and os.environ.get("RESUME") == "1":
        before = min(posts)
        print(f"resuming backfill from #{before}")
    pages = 0
    oldest = None
    while pages < MAX_PAGES:
        url = f"https://t.me/s/{CHANNEL}" + (f"?before={before}" if before else "")
        html = get(url)
        if not html:
            break
        soup = BeautifulSoup(html, "lxml")

        if not meta:
            ti = soup.select_one(".tgme_channel_info_header_title")
            de = soup.select_one(".tgme_channel_info_description")
            ph = soup.select_one(".tgme_page_photo_image img") or soup.select_one(".tgme_channel_info_header_photo img")
            counters = {}
            for c in soup.select(".tgme_channel_info_counter"):
                v = c.select_one(".counter_value")
                t = c.select_one(".counter_type")
                if v and t:
                    counters[t.get_text(strip=True)] = v.get_text(strip=True)
            meta = {"channel": CHANNEL,
                    "title": ti.get_text(strip=True) if ti else CHANNEL,
                    "description": de.get_text("\n", strip=True) if de else "",
                    "avatar": ph.get("src") if ph else None,
                    "counters": counters}

        msgs = soup.select(".tgme_widget_message[data-post]")
        if not msgs:
            break
        ids = []
        for m in msgs:
            p = parse_post(m)
            if p["id"]:
                posts[p["id"]] = p
                ids.append(p["id"])
        pages += 1
        newest_oldest = min(ids) if ids else None
        print(f"page {pages}: +{len(ids)} posts (down to #{newest_oldest}) total={len(posts)}")
        if newest_oldest is None or newest_oldest == oldest:
            break
        oldest = newest_oldest
        before = newest_oldest
        if pages % 25 == 0:
            n = save(path, meta, posts)
            print(f"  checkpoint: {n} posts saved")
        if before <= 1:
            break
        time.sleep(0.6)

    n = save(path, meta, posts)
    print(f"saved {n} posts -> {path}")


if __name__ == "__main__":
    main()
