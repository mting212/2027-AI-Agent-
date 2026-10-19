# -*- coding: utf-8 -*-
import re, pathlib, json, subprocess

RAW = pathlib.Path("raw")
h = (RAW / "yjs_home.html").read_text(encoding="utf-8")
print("len", len(h))
# 找出站内链接模式
links = re.findall(r'href="([^"]+)"', h)
from collections import Counter
pats = Counter()
for l in links:
    pats[re.sub(r'\d+', 'N', l)[:60]] += 1
for p, c in pats.most_common(25):
    print(c, p)
print("\n--- 含 job/招聘 的链接 ---")
for l in links:
    if any(k in l for k in ("job", "zhaopin", "campus", "xiangqing")):
        print(l)
        if len(set(links)) > 50:
            break
