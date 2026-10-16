#!/usr/bin/env python3
"""Merge raw/<City>.<source>.json into docs/events.json: dedupe, drop dead links/past events."""
import json, glob, os, sys, re, datetime, random, urllib.request, concurrent.futures as cf
root = sys.argv[1]
today = datetime.date.today().isoformat()
CENTER = {"Beijing": (39.90, 116.40), "Shanghai": (31.23, 121.47), "Guangzhou": (23.13, 113.26),
          "Shenzhen": (22.54, 114.06), "San Francisco Bay Area": (37.77, -122.42), "New York": (40.71, -74.01),
          "London": (51.51, -0.13), "Singapore": (1.29, 103.85), "Tokyo": (35.68, 139.69)}
def load(p):
    m = re.search(r'\[.*\]', open(p).read(), re.S)
    try: return json.loads(m.group(0)) if m else []
    except Exception: return []
def alive(u):
    for method in ("HEAD", "GET"):
        try:
            r = urllib.request.Request(u, method=method, headers={"User-Agent": "Mozilla/5.0"})
            return urllib.request.urlopen(r, timeout=15).status < 400
        except urllib.error.HTTPError as e:
            if e.code in (403, 429): return True  # bot-blocked but exists
        except Exception: pass
    return False
def near(lat, lng, city):  # AI coords must be within ~1.5 deg of the city, else fall back to center + jitter
    c = CENTER[city]
    try:
        if abs(float(lat) - c[0]) < 1.5 and abs(float(lng) - c[1]) < 1.5: return float(lat), float(lng)
    except (TypeError, ValueError): pass
    return c[0] + random.uniform(-.03, .03), c[1] + random.uniform(-.03, .03)
f = f"{root}/docs/events.json"
rows = [e for e in (json.load(open(f)) if os.path.exists(f) else []) if isinstance(e, dict)]
for p in glob.glob(f"{root}/raw/*.json"):
    city = os.path.basename(p).split(".")[0].replace("_", " ")
    rows += [dict(x, city=city) for x in load(p) if isinstance(x, dict)]
items = {}
for e in rows:
    if e.get("city") not in CENTER or not all(e.get(k) for k in ("title", "start", "url")): continue
    if not str(e["url"]).startswith("http") or str(e["start"])[:10] < today: continue
    key = re.sub(r'\W+', '', e["url"].split('?')[0].lower())
    if key in items: continue
    lat, lng = near(e.get("lat"), e.get("lng"), e["city"])
    items[key] = {k: e.get(k, "") for k in ("title", "start", "location", "category", "url", "city")} | {"lat": round(lat, 5), "lng": round(lng, 5)}
with cf.ThreadPoolExecutor(16) as ex:
    ok = list(ex.map(lambda e: alive(e["url"]), items.values()))
out = sorted((e for e, k in zip(items.values(), ok) if k), key=lambda e: e["start"])
json.dump(out, open(f, "w"), ensure_ascii=False, indent=1)
print(len(out), "events")
