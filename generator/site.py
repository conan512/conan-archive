#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static site generator for the DetectiveConanIR archive (full 9.9k-post scale)."""
import json, os, re, html, shutil, collections, datetime, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from categories import ALL_CATEGORIES, categorize  # noqa
import dashboard as dash  # noqa
sys.path.insert(0, ROOT)
import store  # noqa

DATA = os.path.join(ROOT, "data", "posts.json")
OUT = os.path.join(ROOT, "site")
PER_PAGE = 24
MAX_PAGES_PER_LIST = 40      # cap paginated files per listing (top 960 posts)
TAG_MIN = 3                  # tags with fewer posts get no page (still searchable)
SHARD = 500
CHANNEL = "DetectiveConanIR"
TG = f"https://t.me/{CHANNEL}"


def jdate(iso):
    if not iso:
        return ""
    try:
        return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%Y/%m/%d")
    except Exception:
        return ""


def year_of(iso):
    return (iso or "")[:4] or "?"


def esc(s):
    return html.escape(s or "")


def slug_tag(t):
    s = re.sub(r"[^\w\u0600-\u06FF]+", "-", t.strip().lower()).strip("-")
    return s or "tag"


def thumb(p):
    if p.get("photos"):
        return p["photos"][0]
    for v in p.get("videos", []):
        if v.get("thumb"):
            return v["thumb"]
    if p.get("link") and p["link"].get("image"):
        return p["link"]["image"]
    return p.get("sticker")


CAT_BY_SLUG = {c["slug"]: c for c in ALL_CATEGORIES}

# ---- local media manifest (cdn url -> media/xx/hash.webp) -------------------
import hashlib
MEDIA_SRC = os.path.join(ROOT, "media")
_MAN = {}
_mpath = os.path.join(MEDIA_SRC, "manifest.json")
if os.path.exists(_mpath):
    try:
        _MAN = json.load(open(_mpath, encoding="utf-8")).get("map", {})
    except Exception:
        _MAN = {}


def local(url, depth=0):
    """Return local webp path if downloaded, else the original CDN url."""
    if not url:
        return url
    rel = _MAN.get(hashlib.sha1(url.encode()).hexdigest()[:16])
    return ("../" * depth) + "media/" + rel if rel else url


# Set this to your GoatCounter code (e.g. "conanir") to enable visitor tracking.
# Also set the same value in generator/live.js
GOATCOUNTER = os.environ.get("GOATCOUNTER", "")


def head(title, desc, depth=0):
    up = "../" * depth
    analytics = (
        f'<script data-goatcounter="https://{GOATCOUNTER}.goatcounter.com/count"'
        f' async src="//gc.zgo.at/count.js"></script>' if GOATCOUNTER else
        "<!-- analytics disabled: set GOATCOUNTER env var -->")
    return f"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%95%B5%EF%B8%8F%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
{analytics}
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css">
<link rel="stylesheet" href="{up}assets/theme.css">
</head>
<body>
<div class="fogwrap"><div class="fog a"></div><div class="fog b"></div></div>
"""


def header(active, depth=0):
    up = "../" * depth
    cat_active = any(c["slug"] == active for c in ALL_CATEGORIES)
    catlinks = "".join(
        f'<a class="{"on" if c["slug"] == active else ""}" href="{up}category/{c["slug"]}.html">'
        f'<span class="ci">{c["icon"]}</span>{esc(c["title"])}</a>' for c in ALL_CATEGORIES)

    def top(t, h, k):
        return f'<a class="{"on" if k == active else ""}" href="{h}">{esc(t)}</a>'

    return f"""<header class="site"><div class="wrap hrow">
<a class="brand" href="{up}index.html">
  <span class="lens">\U0001F575\uFE0F</span>
  <span>\u06a9\u0627\u0631\u0622\u06af\u0627\u0647 \u06a9\u0648\u0646\u0627\u0646 \u0627\u06cc\u0631\u0627\u0646<small>DETECTIVE CONAN \u00b7 IR ARCHIVE</small></span>
</a>
<button class="menubtn" aria-label="\u0645\u0646\u0648" onclick="document.querySelector('nav.main').classList.toggle('open')">\u2630</button>
<nav class="main">
  {top("\u062e\u0627\u0646\u0647", up + "index.html", "home")}
  {top("\u0622\u0631\u0634\u06cc\u0648", up + "archive/index.html", "archive")}
  <div class="dd{' on' if cat_active else ''}">
    <button type="button" onclick="this.parentElement.classList.toggle('open')">\U0001F5C2\uFE0F \u0628\u062e\u0634\u200c\u0647\u0627 <span class="car">\u25be</span></button>
    <div class="ddmenu">{catlinks}</div>
  </div>
  {top("\u0647\u0634\u062a\u06af\u200c\u0647\u0627", up + "tags.html", "tags")}
  {top("\U0001F4CA \u062f\u0627\u0634\u0628\u0648\u0631\u062f", up + "dashboard.html", "dashboard")}
</nav>
</div></header>"""


def footer(depth=0, updated=""):
    up = "../" * depth
    cats = "".join(f'<a href="{up}category/{c["slug"]}.html">{c["icon"]} {c["title"]}</a>' for c in ALL_CATEGORIES[:6])
    return f"""<footer class="site"><div class="wrap">
<div class="fgrid">
  <div><h4>🕵️ درباره آرشیو</h4>
    <p>آرشیو کامل و قابل جستجوی کانال تلگرام کارآگاه کونان ایران. هر پست جدید به‌صورت خودکار اینجا ثبت می‌شود.</p></div>
  <div><h4>بخش‌ها</h4>{cats}</div>
  <div><h4>پیوندها</h4>
    <a href="{TG}" target="_blank" rel="noopener">کانال تلگرام</a>
    <a href="https://t.me/ConanIRan" target="_blank" rel="noopener">کانال پشتیبان</a>
    <a href="https://instagram.com/detectiveconan.ir" target="_blank" rel="noopener">اینستاگرام</a>
    <a href="{up}tags.html">فهرست هشتگ‌ها</a></div>
</div>
<div class="fbot">آخرین به‌روزرسانی: {esc(updated)} · محتوا متعلق به کانال @{CHANNEL} است.</div>
</div></footer>
<script>
document.addEventListener('click',e=>{{const n=document.querySelector('nav.main');
if(n&&n.classList.contains('open')&&!e.target.closest('nav.main')&&!e.target.closest('.menubtn'))n.classList.remove('open');
document.querySelectorAll('.dd.open').forEach(d=>{{if(!d.contains(e.target))d.classList.remove('open');}});}});
</script>
</body></html>"""


def post_card(p, depth=1):
    up = "../" * depth
    cat = CAT_BY_SLUG[p["_cat"]]
    im = thumb(p)
    href = f"{up}post.html?id={p['id']}"
    media = ""
    if im:
        n = len(p.get("photos", [])) + len(p.get("videos", []))
        badge = f'<span class="cnt">🖼 {n}</span>' if n > 1 else ""
        play = '<span class="play"><i>▶</i></span>' if p.get("videos") else ""
        media = (f'<a class="pmedia" href="{href}">'
                 f'<img loading="lazy" src="{esc(local(im, depth))}" alt="">{play}{badge}</a>')
    txt = re.sub(r"\n{3,}", "\n\n", p["text"]).strip()
    tags = "".join(f'<a class="tag" href="{up}tag/{slug_tag(t)}.html">#{esc(t)}</a>' for t in p["hashtags"][:5])
    extra = ""
    if p.get("docs"):
        d = p["docs"][0]
        extra = f'<div class="doc"><span>📎</span><span class="dn">{esc(d["name"])}</span><span class="ds">{esc(d["size"])}</span></div>'
    elif p.get("link") and not im:
        l = p["link"]
        extra = f'<div class="lnkprev"><b>{esc(l["title"] or l["site"])}</b><span>{esc(l["desc"])}</span></div>'
    elif p.get("voice"):
        extra = '<div class="doc"><span>🎙</span><span class="dn">پیام صوتی</span></div>'
    elif p.get("audio"):
        a = p["audio"]
        extra = f'<div class="doc"><span>🎵</span><span class="dn">{esc(a["title"] or "فایل صوتی")}</span><span class="ds">{esc(a["author"])}</span></div>'
    return f"""<article class="post{'' if im else ' noimg'}">{media}
<div class="pbody">
  <a class="pcat" href="{up}category/{cat['slug']}.html">{cat['icon']} {esc(cat['title'])}</a>
  {extra}
  <a class="ptext" href="{href}">{esc(txt)}</a>
  <div class="tags">{tags}</div>
  <div class="pfoot"><span>🗓 {jdate(p['date'])}</span>{f"<span>👁 {esc(p['views'])}</span>" if p['views'] else ""}
    <a class="tg" href="{esc(p['url'])}" target="_blank" rel="noopener">تلگرام ↗</a></div>
</div></article>"""


def pager(cur, total, fmt, capped=False):
    if total <= 1:
        return ""
    out = []
    if cur > 1:
        out.append(f'<a href="{fmt(cur-1)}">‹ قبلی</a>')
    show = {1, total, cur, cur - 1, cur + 1, cur - 2, cur + 2}
    last = 0
    for i in sorted(x for x in show if 1 <= x <= total):
        if i - last > 1:
            out.append('<span class="dots">…</span>')
        out.append(f'<span class="cur">{i}</span>' if i == cur else f'<a href="{fmt(i)}">{i}</a>')
        last = i
    if cur < total:
        out.append(f'<a href="{fmt(cur+1)}">بعدی ›</a>')
    note = ('<div class="note">برای دیدن پست‌های قدیمی‌تر این بخش از <b>جستجوی صفحهٔ اصلی</b> '
            'یا صفحات هشتگ استفاده کنید.</div>') if capped else ""
    return f'<div class="pager">{"".join(out)}</div>{note}'


def write(path, content):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(content)


def build():
    meta, pmap, upd = store.load()
    posts = list(pmap.values())
    if not posts:
        sys.exit("no posts found — run scraper/fetch.py first")
    updated = jdate(upd)
    for p in posts:
        p["_cat"] = categorize(p)
    posts.sort(key=lambda x: -x["id"])

    by_cat, by_tag, by_year = collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(list)
    tag_names = {}
    for p in posts:
        by_cat[p["_cat"]].append(p)
        by_year[year_of(p["date"])].append(p)
        for t in p["hashtags"]:
            s = slug_tag(t)
            by_tag[s].append(p)
            tag_names.setdefault(s, t)

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    shutil.copy(os.path.join(HERE, "theme.css"), os.path.join(OUT, "assets", "theme.css"))
    shutil.copy(os.path.join(HERE, "live.js"), os.path.join(OUT, "assets", "live.js"))
    if os.path.isdir(MEDIA_SRC) and _MAN:
        dst = os.path.join(OUT, "media")
        if os.environ.get("COPY_MEDIA") == "1":
            if os.path.exists(dst) and not os.path.islink(dst):
                shutil.rmtree(dst)
            elif os.path.islink(dst):
                os.unlink(dst)
            shutil.copytree(MEDIA_SRC, dst, ignore=shutil.ignore_patterns("*.tmp", "manifest.json"))
            print(f"  copied {len(_MAN):,} local images")
        else:
            # local preview: symlink instead of duplicating 12k files
            if os.path.islink(dst) or os.path.exists(dst):
                (os.unlink if os.path.islink(dst) else shutil.rmtree)(dst)
            os.symlink(os.path.relpath(MEDIA_SRC, OUT), dst)
            print(f"  linked {len(_MAN):,} local images (set COPY_MEDIA=1 to copy)")

    # ---------- sharded full data for client-rendered post pages ----------
    shards = collections.defaultdict(dict)
    for p in posts:
        q = {k: p[k] for k in ("id", "url", "date", "text", "hashtags", "photos", "videos",
                               "docs", "views", "voice", "audio", "link", "sticker", "forwarded", "_cat")}
        q["photos"] = [local(u, 0) for u in (q.get("photos") or [])]
        q["videos"] = [{**v, "thumb": local(v.get("thumb"), 0)} for v in (q.get("videos") or [])]
        if q.get("sticker"):
            q["sticker"] = local(q["sticker"], 0)
        if q.get("link") and q["link"].get("image"):
            q["link"] = {**q["link"], "image": local(q["link"]["image"], 0)}
        shards[p["id"] // SHARD][str(p["id"])] = q
    for k, v in shards.items():
        write(f"data/{k}.json", json.dumps(v, ensure_ascii=False, separators=(",", ":")))

    # ---------- search index ----------
    idx = [{"i": p["id"], "t": p["text"][:220], "h": p["hashtags"], "c": p["_cat"],
            "d": jdate(p["date"]), "m": local(thumb(p), 0) or "", "v": 1 if p.get("videos") else 0} for p in posts]
    write("assets/index.json", json.dumps(idx, ensure_ascii=False, separators=(",", ":")))
    catmap = {c["slug"]: {"t": c["title"], "i": c["icon"]} for c in ALL_CATEGORIES}
    write("assets/cats.json", json.dumps(catmap, ensure_ascii=False))

    # ---------- home ----------
    c = meta.get("counters", {})
    stats = [(c.get("subscribers", "—"), "دنبال‌کننده"), (f"{len(posts):,}", "پست آرشیوی"),
             (f"{sum(1 for p in posts if p['photos']):,}", "پست تصویری"),
             (f"{sum(1 for p in posts if p['videos']):,}", "پست ویدیویی"),
             (f"{len(by_tag):,}", "هشتگ")]
    statshtml = "".join(f'<div class="stat"><b>{esc(a)}</b><span>{b}</span></div>' for a, b in stats)
    catcards = "".join(
        f'''<a class="catcard" href="category/{ct["slug"]}.html">
<div class="ic">{ct["icon"]}</div><h3>{esc(ct["title"])}</h3><p>{esc(ct["desc"])}</p>
<div class="n">{len(by_cat.get(ct["slug"], [])):,} پست</div></a>''' for ct in ALL_CATEGORIES)
    latest = "".join(post_card(p, 0) for p in posts[:12])
    top_tags = sorted(by_tag.items(), key=lambda kv: -len(kv[1]))[:36]
    cloud = "".join(f'<a href="tag/{s}.html">#{esc(tag_names[s])}<b>{len(v)}</b></a>' for s, v in top_tags)
    years = sorted((y for y in by_year if y.isdigit()), reverse=True)
    yearbar = "".join(f'<a href="year/{y}.html">{y}<b>{len(by_year[y])}</b></a>' for y in years)

    write("index.html", head("کارآگاه کونان ایران — آرشیو کامل کانال",
                             "آرشیو کامل، دسته‌بندی‌شده و قابل جستجوی کانال تلگرام Detective Conan .IR") +
          header("home", 0) + f"""
<section class="hero"><div class="glow"></div><div class="wrap">
  {f'<img class="avatar" src="{esc(local(meta["avatar"], 0))}" alt="لوگو">' if meta.get("avatar") else ""}
  <h1>پرونده‌های کارآگاه کونان</h1>
  <p class="sub">آرشیو کامل کانال <b>@{CHANNEL}</b> از سال ۲۰۲۰ تا امروز — هر پست، هر کپشن، هر هشتگ.</p>
  <div class="stats">{statshtml}</div>
  <div class="searchbar"><input id="q" type="search" placeholder="جستجو در {len(posts):,} پست…" autocomplete="off"><span class="ico">🔍</span></div>
</div></section>
<main class="wrap">
  <div id="results" style="display:none"><div class="sechead"><h2>🔎 نتایج جستجو</h2><div class="ln"></div>
    <span id="rc" style="font-size:.83rem;color:var(--dim)"></span></div><div class="grid" id="rgrid"></div></div>
  <div id="normal">
    <div class="sechead"><h2>🗂️ بخش‌های سایت</h2><div class="ln"></div></div>
    <div class="catgrid">{catcards}</div>
    <div class="sechead"><h2>📅 مرور بر اساس سال</h2><div class="ln"></div></div>
    <div class="yearbar">{yearbar}</div>
    <div class="sechead"><h2>🆕 تازه‌ترین پرونده‌ها</h2><div class="ln"></div><a class="more" href="archive/index.html">همه پست‌ها ←</a></div>
    <div class="grid">{latest}</div>
    <div class="sechead"><h2>🏷️ هشتگ‌های پرتکرار</h2><div class="ln"></div><a class="more" href="tags.html">همه هشتگ‌ها ←</a></div>
    <div class="cloud">{cloud}</div>
  </div>
</main>
<script src="assets/search.js" defer></script>""" + footer(0, updated))

    write("assets/search.js", """
let DATA=null,CATS=null;
const q=document.getElementById('q'),res=document.getElementById('results'),
      nor=document.getElementById('normal'),grid=document.getElementById('rgrid'),rc=document.getElementById('rc');
async function load(){if(!DATA){rc.textContent='در حال بارگذاری فهرست…';
  [DATA,CATS]=await Promise.all([fetch('assets/index.json').then(r=>r.json()),fetch('assets/cats.json').then(r=>r.json())]);}
  return DATA}
const E=s=>s.replace(/[<>&]/g,x=>({'<':'&lt;','>':'&gt;','&':'&amp;'}[x]));
function card(p){const c=(CATS&&CATS[p.c])||{t:'',i:''};
 const media=p.m?`<a class="pmedia" href="post.html?id=${p.i}"><img loading="lazy" src="${p.m}">${p.v?'<span class="play"><i>▶</i></span>':''}</a>`:'';
 const tags=(p.h||[]).slice(0,5).map(t=>`<a class="tag" href="tag/${slug(t)}.html">#${E(t)}</a>`).join('');
 return `<article class="post${p.m?'':' noimg'}">${media}<div class="pbody">
 <span class="pcat">${c.i} ${c.t}</span>
 <a class="ptext" href="post.html?id=${p.i}">${E(p.t)}</a>
 <div class="tags">${tags}</div><div class="pfoot"><span>🗓 ${p.d}</span>
 <a class="tg" href="https://t.me/DetectiveConanIR/${p.i}" target="_blank">تلگرام ↗</a></div></div></article>`}
function slug(t){return t.trim().toLowerCase().replace(/[^\\w\\u0600-\\u06FF]+/g,'-').replace(/^-|-$/g,'')||'tag'}
let tmr;
q&&q.addEventListener('input',()=>{clearTimeout(tmr);tmr=setTimeout(run,220)});
async function run(){const s=q.value.trim().toLowerCase();
 if(s.length<2){res.style.display='none';nor.style.display='';return}
 res.style.display='';nor.style.display='none';
 const d=await load();
 const bare=s.replace('#','');
 const hit=d.filter(p=>p.t.toLowerCase().includes(s)||(p.h||[]).some(h=>h.toLowerCase().includes(bare)));
 rc.textContent=hit.length.toLocaleString('fa')+' پست پیدا شد'+(hit.length>90?' (۹۰ مورد اول)':'');
 grid.innerHTML=hit.length?hit.slice(0,90).map(card).join(''):
  '<div class="empty" style="grid-column:1/-1"><div class="big">🔍</div>پرونده‌ای با این عبارت پیدا نشد.</div>'}
const pre=new URLSearchParams(location.search).get('q');
if(pre&&q){q.value=pre;run()}
""")

    # ---------- post.html (client-rendered detail) ----------
    write("post.html", head("پست — کارآگاه کونان ایران", "نمایش پست", 0) + header("", 0) + f"""
<main class="wrap"><div id="app"><div class="empty"><div class="big">🕵️</div>در حال باز کردن پرونده…</div></div></main>
<script>
const SHARD={SHARD};
const E=s=>(s||'').replace(/[<>&]/g,x=>({{'<':'&lt;','>':'&gt;','&':'&amp;'}}[x]));
function slug(t){{return t.trim().toLowerCase().replace(/[^\\w\\u0600-\\u06FF]+/g,'-').replace(/^-|-$/g,'')||'tag'}}
function linkify(t){{return E(t)
 .replace(/(https?:\\/\\/[^\\s<]+)/g,'<a class="tag" href="$1" target="_blank" rel="noopener">$1</a>')
 .replace(/#([\\w\\u0600-\\u06FF_]+)/g,(m,g)=>`<a class="tag" href="tag/${{slug(g)}}.html">#${{g}}</a>`)
 .replace(/@([A-Za-z]\\w{{3,}})/g,'<a class="tag" href="https://t.me/$1" target="_blank" rel="noopener">@$1</a>')}}
(async()=>{{
 const id=+new URLSearchParams(location.search).get('id');
 const app=document.getElementById('app');
 if(!id){{app.innerHTML='<div class="empty"><div class="big">🔍</div>شناسهٔ پست نامعتبر است.</div>';return}}
 let cats={{}},p=null;
 try{{
   const [sh,cm]=await Promise.all([
     fetch('data/'+Math.floor(id/SHARD)+'.json').then(r=>r.json()),
     fetch('assets/cats.json').then(r=>r.json())]);
   p=sh[id];cats=cm;
 }}catch(e){{}}
 if(!p){{app.innerHTML='<div class="empty"><div class="big">🗂️</div><h2>این پرونده در بایگانی نیست</h2>'+
   '<p style="margin-top:14px"><a class="btn" href="https://t.me/{CHANNEL}/'+id+'" target="_blank">دیدن در تلگرام ↗</a></p></div>';return}}
 const c=cats[p._cat]||{{t:'',i:''}};
 let gal=(p.photos||[]).map(u=>`<img loading="lazy" src="${{u}}">`).join('');
 (p.videos||[]).forEach(v=>{{
   if(v.src)gal+=`<video controls preload="none" poster="${{v.thumb||''}}" style="width:100%;border-radius:12px;border:1px solid var(--line)"><source src="${{v.src}}"></video>`;
   else if(v.thumb)gal+=`<a href="${{p.url}}" target="_blank" style="position:relative;display:block"><img src="${{v.thumb}}"><span class="play" style="position:absolute;inset:0;display:grid;place-items:center"><i style="width:54px;height:54px;border-radius:50%;display:grid;place-items:center;background:rgba(216,31,54,.9);color:#fff;font-style:normal">▶</i></span></a>`}});
 const docs=(p.docs||[]).map(x=>`<div class="doc"><span>📎</span><span class="dn">${{E(x.name)}}</span><span class="ds">${{E(x.size)}}</span></div>`).join('');
 const lnk=p.link?`<a class="lnkprev" style="display:block;margin-top:16px" href="${{p.link.url||'#'}}" target="_blank"><b>${{E(p.link.title||p.link.site)}}</b><span>${{E(p.link.desc)}}</span></a>`:'';
 const tags=(p.hashtags||[]).map(t=>`<a class="tag" href="tag/${{slug(t)}}.html">#${{E(t)}}</a>`).join('');
 const dt=(p.date||'').slice(0,10).replace(/-/g,'/');
 document.title=(p.text||'').split('\\n')[0].slice(0,60)+' — کارآگاه کونان ایران';
 app.innerHTML=`<article class="article">
  <div class="hd"><a class="pcat" href="category/${{p._cat}}.html">${{c.i}} ${{c.t}}</a>
   <span style="color:var(--faint);font-size:.82rem">🗓 ${{dt}}</span>
   ${{p.views?`<span style="color:var(--faint);font-size:.82rem">👁 ${{E(p.views)}}</span>`:''}}
   <a class="btn" style="margin-inline-start:auto" href="${{p.url}}" target="_blank">مشاهده در تلگرام ↗</a></div>
  <div class="body">${{gal?`<div class="gal">${{gal}}</div>`:''}}${{docs}}
   <div class="txt">${{linkify(p.text||'')}}</div>${{lnk}}
   <div class="tags" style="margin-top:20px">${{tags}}</div></div></article>
  <div style="display:flex;gap:10px;flex-wrap:wrap">
   <a class="backlink" href="post.html?id=${{id+1}}">پست بعدی ›</a>
   <a class="backlink" href="post.html?id=${{id-1}}">‹ پست قبلی</a>
   <a class="backlink" href="archive/index.html">بازگشت به آرشیو</a></div>`;
}})();
</script>""" + footer(0, updated))

    # ---------- listings ----------
    def listing(items, title, subtitle, icon, folder, base, depth, active, extra_html=""):
        total_all = max(1, (len(items) + PER_PAGE - 1) // PER_PAGE)
        pages = min(total_all, MAX_PAGES_PER_LIST)
        for i in range(1, pages + 1):
            chunk = items[(i - 1) * PER_PAGE: i * PER_PAGE]
            fname = f"{base}.html" if i == 1 else f"{base}-{i}.html"
            fmt = lambda n: (f"{base}.html" if n == 1 else f"{base}-{n}.html")
            body = "".join(post_card(p, depth) for p in chunk) or \
                '<div class="empty" style="grid-column:1/-1"><div class="big">🗂️</div>هنوز پستی در این بخش ثبت نشده.</div>'
            write(f"{folder}/{fname}" if folder else fname,
                  head(f"{title} — کارآگاه کونان ایران", subtitle, depth) + header(active, depth) + f"""
<main class="wrap">
  <div class="sechead"><h2>{icon} {esc(title)}</h2><div class="ln"></div>
    <span style="font-size:.83rem;color:var(--dim)">{len(items):,} پست{f' · صفحه {i} از {pages}' if pages > 1 else ''}</span></div>
  <p style="color:var(--dim);font-size:.9rem;margin-bottom:18px">{esc(subtitle)}</p>
  {extra_html}
  <div class="grid">{body}</div>
  {pager(i, pages, fmt, capped=(i == pages and total_all > pages))}
</main>""" + footer(depth, updated))

    yb = f'<div class="yearbar">{"".join(f0 for f0 in (f"<a href=\"../year/{y}.html\">{y}<b>{len(by_year[y])}</b></a>" for y in years))}</div>'
    listing(posts, "آرشیو کامل", "همهٔ پست‌های کانال، از تازه‌ترین به قدیمی‌ترین.", "📚",
            "archive", "index", 1, "archive", yb)
    for ct in ALL_CATEGORIES:
        listing(by_cat.get(ct["slug"], []), ct["title"], ct["desc"], ct["icon"],
                "category", ct["slug"], 1, ct["slug"])
    for y in years:
        listing(by_year[y], f"آرشیو سال {y}", f"همهٔ پست‌های منتشرشده در سال {y}.", "📅",
                "year", y, 1, "archive", yb)

    kept = {s: v for s, v in by_tag.items() if len(v) >= TAG_MIN}
    for s, items in kept.items():
        listing(items, f"#{tag_names[s]}", f"پست‌های دارای هشتگ #{tag_names[s]} در کانال.", "🏷️",
                "tag", s, 1, "tags")

    # ---------- dashboard ----------
    st = dash.build_stats(posts, by_cat, by_tag, by_year, CAT_BY_SLUG, jdate)

    kpis = [
        ("\U0001F4C4", f"{st['total_posts']:,}", "پست آرشیوی"),
        ("\U0001F441", f"{st['total_views']:,}", "مجموع بازدید تلگرام"),
        ("\U0001F4C8", f"{st['avg']:,.0f}", "میانگین بازدید هر پست"),
        ("\U0001F3C6", f"{st['max']:,}", "بیشترین بازدید"),
        ("\U0001F3F7", f"{st['n_tags']:,}", "هشتگ یکتا"),
        ("\U0001F5C2", f"{len(ALL_CATEGORIES)}", "بخش موضوعی"),
    ]
    kpihtml = "".join(
        f'<div class="kpi"><div class="ki">{i}</div><b>{v}</b><span>{l}</span></div>'
        for i, v, l in kpis)

    ys = sorted(st["years"].items())
    year_chart = dash.bar_chart([(y, d["n"]) for y, d in ys], " پست")
    yearv_chart = dash.bar_chart([(y, int(d["views"])) for y, d in ys], " بازدید", "var(--gold)")
    mon_chart = dash.bar_chart([(m[5:7], n) for m, n in st["months"]], " پست", "var(--blue)")

    dowlabels = ["دو", "سه", "چه", "پن", "جم", "شن", "یک"]
    dow_chart = dash.bar_chart([(dowlabels[i], st["dows"].get(i, 0)) for i in range(7)],
                               " پست", "var(--blue)")
    hour_chart = dash.bar_chart([(f"{h:02d}", st["hours"].get(h, 0)) for h in range(24)],
                                " پست", "var(--red)")

    mcols = ["#d81f36", "#4d8fd6", "#e2b857", "#6c7a99"]
    mlabels = {"photo": "تصویری", "video": "ویدیویی", "doc": "فایل", "text": "متنی"}
    mparts = [(mlabels[k], v, mcols[i]) for i, (k, v) in enumerate(st["media"].items())]
    mlegend = "".join(
        f'<div class="lg"><i style="background:{c}"></i>{l}<b>{v:,}</b></div>'
        for l, v, c in mparts)

    _mxn = st["cats"][0]["n"] if st["cats"] else 1
    catrows = "".join(
        '<tr><td><a href="category/{s}.html">{ic} {t}</a></td><td>{n:,}</td>'
        '<td>{vw:,}</td><td>{av:,.0f}</td>'
        '<td><div class="mini"><i style="width:{pc:.0f}%"></i></div></td></tr>'.format(
            s=c["slug"], ic=c["icon"], t=esc(c["title"]), n=c["n"],
            vw=int(c["views"]), av=c["avg"], pc=c["n"] / _mxn * 100)
        for c in st["cats"])

    toprows = "".join(
        '<tr><td class="rk">{i}</td><td><a href="post.html?id={pid}">{txt}</a></td>'
        '<td>{dt}</td><td class="vw">{v:,}</td></tr>'.format(
            i=i + 1, pid=p2["id"],
            txt=esc((p2["text"].split("\n")[0] or "پست")[:58]),
            dt=jdate(p2["date"]), v=p2["_v"])
        for i, p2 in enumerate(st["top_posts"]))

    tagrows = "".join(
        f'<a href="tag/{s2}.html">#{esc(tag_names[s2])}<b>{len(v):,}</b></a>'
        for s2, v in st["top_tags"])

    _dash_body = """
<main class="wrap">
  <div class="sechead"><h2>\U0001F4CA داشبورد آمار</h2><div class="ln"></div>
    <span style="font-size:.83rem;color:var(--dim)">به‌روزرسانی: {upd}</span></div>

  <div class="kpis">{kpis}</div>

  <div class="dgrid">
    <div class="card"><h3>\U0001F4C5 پست‌ها در هر سال</h3>{yearc}</div>
    <div class="card"><h3>\U0001F441 بازدید در هر سال</h3>{yearv}</div>
  </div>

  <div class="card"><h3>\U0001F4C8 فعالیت ۲۴ ماه اخیر</h3>{monc}</div>

  <div class="dgrid">
    <div class="card"><h3>\U0001F5BC ترکیب محتوا</h3>
      <div class="dnt">{donut}<div class="lgs">{mlegend}</div></div></div>
    <div class="card"><h3>\U0001F4C6 روزهای هفته</h3>{dowc}</div>
  </div>

  <div class="card"><h3>\U0001F551 ساعت انتشار (UTC)</h3>{hourc}</div>

  <div class="card"><h3>\U0001F5C2 عملکرد بخش‌ها</h3>
    <div class="tblwrap"><table class="dtbl">
      <thead><tr><th>بخش</th><th>پست</th><th>بازدید</th><th>میانگین</th><th></th></tr></thead>
      <tbody>{catrows}</tbody></table></div></div>

  <div class="card"><h3>\U0001F3C6 پربازدیدترین پست‌ها</h3>
    <div class="tblwrap"><table class="dtbl">
      <thead><tr><th>#</th><th>پست</th><th>تاریخ</th><th>بازدید</th></tr></thead>
      <tbody>{toprows}</tbody></table></div></div>

  <div class="card"><h3>\U0001F3F7 پرتکرارترین هشتگ‌ها</h3>
    <div class="cloud">{tagrows}</div></div>

  <div class="card" id="live">
    <h3>\U0001F310 آمار بازدیدکنندگان سایت</h3>
    <div id="livebox"><div class="note" style="margin:0">
      برای دیدن آمار زندهٔ بازدیدکنندگان، سرویس آمار را فعال کنید.
      راهنمای کامل در فایل <b>راهنمای-داشبورد.md</b> آمده است.
    </div></div>
  </div>
</main>
<script src="assets/live.js" defer></script>""".format(
        upd=esc(updated), kpis=kpihtml, yearc=year_chart, yearv=yearv_chart,
        monc=mon_chart, donut=dash.donut(mparts), mlegend=mlegend, dowc=dow_chart,
        hourc=hour_chart, catrows=catrows, toprows=toprows, tagrows=tagrows)

    write("dashboard.html",
          head("داشبورد آمار — کارآگاه کونان ایران", "آمار کامل محتوا و بازدید", 0) +
          header("dashboard", 0) + _dash_body + footer(0, updated))

    allt = sorted(kept.items(), key=lambda kv: -len(kv[1]))
    cloud2 = "".join(f'<a href="tag/{s}.html">#{esc(tag_names[s])}<b>{len(v)}</b></a>' for s, v in allt)
    write("tags.html", head("همه هشتگ‌ها — کارآگاه کونان ایران", "فهرست کامل هشتگ‌های کانال", 0) +
          header("tags", 0) + f"""
<main class="wrap">
  <div class="sechead"><h2>🏷️ هشتگ‌ها</h2><div class="ln"></div>
    <span style="font-size:.83rem;color:var(--dim)">{len(allt):,} هشتگ دارای صفحه · مجموع {len(by_tag):,}</span></div>
  <p style="color:var(--dim);font-size:.9rem;margin-bottom:18px">هشتگ‌هایی که حداقل {TAG_MIN} پست دارند صفحهٔ اختصاصی دارند؛ بقیه از طریق جستجو در دسترس‌اند.</p>
  <div class="cloud">{cloud2}</div>
</main>""" + footer(0, updated))

    items = "".join(f"""<item><title>{esc((p['text'].split(chr(10))[0] or 'پست')[:80])}</title>
<link>{esc(p['url'])}</link><guid isPermaLink="false">{p['id']}</guid>
<pubDate>{esc(p['date'] or '')}</pubDate><description>{esc(p['text'][:400])}</description></item>""" for p in posts[:50])
    write("rss.xml", f"""<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>
<title>{esc(meta.get('title', CHANNEL))}</title><link>{TG}</link>
<description>{esc(meta.get('description', '')[:200])}</description>{items}</channel></rss>""")
    write("sitemap.txt", "\n".join(["index.html", "tags.html", "archive/index.html"] +
                                   [f"category/{c['slug']}.html" for c in ALL_CATEGORIES] +
                                   [f"year/{y}.html" for y in years] +
                                   [f"tag/{s}.html" for s in kept]))
    write("404.html", head("پرونده پیدا نشد", "404", 0) + header("", 0) +
          '<main class="wrap"><div class="empty"><div class="big">🔍</div><h2>این پرونده در بایگانی نیست</h2>'
          '<p style="margin-top:10px"><a class="btn" href="index.html">بازگشت به خانه</a></p></div></main>'
          + footer(0, updated))
    write(".nojekyll", "")

    nfiles = sum(len(f) for _, _, f in os.walk(OUT))
    print(f"✓ {len(posts):,} posts · {len(ALL_CATEGORIES)} categories · {len(kept):,} tag pages · "
          f"{len(years)} years · {nfiles:,} files")


if __name__ == "__main__":
    build()
