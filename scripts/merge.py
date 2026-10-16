#!/usr/bin/env python3
"""Merge raw/*.json (one per AI source) into site/events.json: dedupe, drop dead links/past events."""
import json, glob, sys, re, datetime, urllib.request, concurrent.futures as cf
root = sys.argv[1]
today = datetime.date.today().isoformat()
def load(p):
    t = open(p).read()
    m = re.search(r'\[.*\]', t, re.S)
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
old = json.load(open(f"{root}/site/events.json")) if glob.glob(f"{root}/site/events.json") else []
items = {}
for e in old + [x for p in glob.glob(f"{root}/raw/*.json") for x in load(p)]:
    if not isinstance(e, dict) or not all(e.get(k) for k in ("title", "start", "url")): continue
    if not str(e["url"]).startswith("http") or str(e["start"])[:10] < today: continue
    key = re.sub(r'\W+', '', e["url"].split('?')[0].lower()) or e["title"].lower()
    items.setdefault(key, {k: e.get(k, "") for k in ("title", "start", "location", "category", "url")})
with cf.ThreadPoolExecutor(16) as ex:
    ok = list(ex.map(lambda e: alive(e["url"]), items.values()))
out = sorted((e for e, k in zip(items.values(), ok) if k), key=lambda e: e["start"])
json.dump(out, open(f"{root}/site/events.json", "w"), ensure_ascii=False, indent=1)
print(len(out), "events")
