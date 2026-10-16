#!/usr/bin/env python3
"""Merge raw/<City>.<source>.json into docs/events.json: dedupe, drop dead links/past events."""
import json, glob, os, sys, re, datetime, urllib.request, urllib.parse, concurrent.futures as cf
root = sys.argv[1]
today = datetime.date.today().isoformat()
CITIES = {"San Francisco Bay Area", "Beijing", "Shanghai"}
def load(p):
    m = re.search(r'\[.*\]', open(p).read(), re.S)
    try: return json.loads(m.group(0)) if m else []
    except Exception: return []
def check(u):  # "ok" = opened, "unsure" = site blocks bots (403/429), None = dead
    for method in ("HEAD", "GET"):
        try:
            r = urllib.request.Request(u, method=method, headers={"User-Agent": "Mozilla/5.0"})
            if urllib.request.urlopen(r, timeout=15).status < 400: return "ok"
        except urllib.error.HTTPError as e:
            if e.code in (403, 429): return "unsure"
        except Exception: pass
    return None
f = f"{root}/docs/events.json"
rows = [e for e in (json.load(open(f)) if os.path.exists(f) else []) if isinstance(e, dict)]
for p in glob.glob(f"{root}/raw/*.json"):
    city = os.path.basename(p).split(".")[0].replace("_", " ")
    rows += [dict(x, city=city) for x in load(p) if isinstance(x, dict)]
items = {}
for e in rows:
    if e.get("city") not in CITIES or not all(e.get(k) for k in ("title", "start", "url")): continue
    if not str(e["url"]).startswith("http") or str(e["start"])[:10] < today: continue
    key = re.sub(r'\W+', '', e["url"].split('?')[0].lower())
    if key in items:  # duplicate: only use it to fill a missing price
        if items[key]["price"] == "Unknown" and e.get("price"): items[key]["price"] = e["price"]
        continue
    site = urllib.parse.urlparse(e["url"]).netloc.removeprefix("www.")
    items[key] = {k: e.get(k, "") for k in ("title", "start", "url", "city")} | {"price": e.get("price") or "Unknown", "site": site}
with cf.ThreadPoolExecutor(16) as ex:
    st = list(ex.map(lambda e: check(e["url"]), items.values()))
out = sorted((e | {"link": s} for e, s in zip(items.values(), st) if s), key=lambda e: e["start"])
json.dump(out, open(f, "w"), ensure_ascii=False, indent=1)
print(len(out), "events")
