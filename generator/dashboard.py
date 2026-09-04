# -*- coding: utf-8 -*-
"""Analytics dashboard: content stats from the archive + live visitor stats."""
import collections, json, re


def vnum(v):
    """'1.5K' -> 1500"""
    v = (v or "").strip().replace(",", "").replace("\u200c", "")
    if not v:
        return 0
    mult = {"K": 1000, "M": 1000000, "k": 1000, "m": 1000000}
    if v[-1] in mult:
        try:
            return int(float(v[:-1]) * mult[v[-1]])
        except ValueError:
            return 0
    try:
        return int(v)
    except ValueError:
        return 0


def fa(n):
    return f"{n:,}"


def build_stats(posts, by_cat, by_tag, by_year, CAT_BY_SLUG, jdate):
    """Everything the dashboard needs, computed from the archive."""
    for p in posts:
        p["_v"] = vnum(p.get("views"))
    seen = [p for p in posts if p["_v"] > 0]
    total_v = sum(p["_v"] for p in seen)
    avg = total_v / len(seen) if seen else 0
    srt = sorted(p["_v"] for p in seen)
    median = srt[len(srt) // 2] if srt else 0

    # per-year views + counts
    ydata = {}
    for y, items in by_year.items():
        if not y.isdigit():
            continue
        vv = [p["_v"] for p in items if p["_v"]]
        ydata[y] = {"n": len(items), "views": sum(vv),
                    "avg": (sum(vv) / len(vv)) if vv else 0}

    # per-category
    cdata = []
    for slug, items in by_cat.items():
        vv = [p["_v"] for p in items if p["_v"]]
        c = CAT_BY_SLUG[slug]
        cdata.append({"slug": slug, "title": c["title"], "icon": c["icon"],
                      "n": len(items), "views": sum(vv),
                      "avg": (sum(vv) / len(vv)) if vv else 0})
    cdata.sort(key=lambda x: -x["n"])

    # media mix
    media = {"photo": 0, "video": 0, "doc": 0, "text": 0}
    for p in posts:
        if p.get("videos"):
            media["video"] += 1
        elif p.get("photos"):
            media["photo"] += 1
        elif p.get("docs"):
            media["doc"] += 1
        else:
            media["text"] += 1

    # monthly activity, last 24 months
    monthly = collections.Counter()
    for p in posts:
        d = (p.get("date") or "")[:7]
        if d:
            monthly[d] += 1
    months = sorted(monthly)[-24:]

    # posting rhythm
    dows = collections.Counter()
    hours = collections.Counter()
    for p in posts:
        d = p.get("date") or ""
        if len(d) >= 13:
            try:
                import datetime
                dt = datetime.datetime.fromisoformat(d.replace("Z", "+00:00"))
                dows[dt.weekday()] += 1
                hours[dt.hour] += 1
            except Exception:
                pass

    top_posts = sorted(seen, key=lambda p: -p["_v"])[:15]
    top_tags = sorted(by_tag.items(), key=lambda kv: -len(kv[1]))[:15]

    return {
        "total_posts": len(posts),
        "total_views": total_v,
        "avg": avg,
        "median": median,
        "max": srt[-1] if srt else 0,
        "with_views": len(seen),
        "years": ydata,
        "cats": cdata,
        "media": media,
        "months": [(m, monthly[m]) for m in months],
        "dows": dows,
        "hours": hours,
        "top_posts": top_posts,
        "top_tags": top_tags,
        "n_tags": len(by_tag),
    }


def bar_chart(pairs, unit="", color="var(--red)", height=150):
    """Inline SVG bar chart. pairs = [(label, value)]"""
    if not pairs:
        return ""
    mx = max(v for _, v in pairs) or 1
    n = len(pairs)
    w = max(520, n * 34)
    bw = w / n * 0.62
    gap = w / n
    bars = []
    for i, (lab, v) in enumerate(pairs):
        h = (v / mx) * (height - 30)
        x = i * gap + (gap - bw) / 2
        y = height - 22 - h
        bars.append(
            f'<g><rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{max(h,1):.1f}" rx="3" '
            f'fill="{color}" opacity=".78"><title>{lab}: {v:,}{unit}</title></rect>'
            f'<text x="{x + bw/2:.1f}" y="{height-8}" text-anchor="middle" '
            f'font-size="9" fill="#5d6883">{lab}</text></g>')
    return (f'<svg viewBox="0 0 {w} {height}" preserveAspectRatio="none" '
            f'style="width:100%;height:{height}px;overflow:visible">{"".join(bars)}</svg>')


def donut(parts, size=150):
    """parts = [(label, value, color)]"""
    total = sum(v for _, v, _ in parts) or 1
    r, cx = size / 2 - 14, size / 2
    circ = 2 * 3.14159 * r
    off = 0
    segs = []
    for lab, v, col in parts:
        frac = v / total
        segs.append(
            f'<circle cx="{cx}" cy="{cx}" r="{r}" fill="none" stroke="{col}" stroke-width="18" '
            f'stroke-dasharray="{circ*frac:.2f} {circ:.2f}" stroke-dashoffset="{-off:.2f}" '
            f'transform="rotate(-90 {cx} {cx})"><title>{lab}: {v:,} ({frac*100:.0f}%)</title></circle>')
        off += circ * frac
    return f'<svg viewBox="0 0 {size} {size}" style="width:{size}px;height:{size}px">{"".join(segs)}</svg>'
