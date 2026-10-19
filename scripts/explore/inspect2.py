# -*- coding: utf-8 -*-
import json, subprocess, re, urllib.parse, pathlib
from html import unescape

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
RAW = pathlib.Path("raw")


def curl(url, post=None, form=None, referer=None, save=None):
    cmd = ["curl.exe", "-s", "-L", "--compressed", "--max-time", "30", "-A", UA,
           "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8"]
    if referer:
        cmd += ["-H", "Referer: " + referer]
    if post is not None:
        cmd += ["-X", "POST", "-H", "Content-Type: application/json;charset=UTF-8",
                "--data", json.dumps(post, ensure_ascii=False)]
    if form is not None:
        cmd += ["-X", "POST", "-H", "Content-Type: application/x-www-form-urlencoded",
                "--data", urllib.parse.urlencode(form)]
    cmd.append(url)
    p = subprocess.run(cmd, capture_output=True)
    txt = p.stdout.decode("utf-8", "replace")
    if save:
        (RAW / save).write_text(txt, encoding="utf-8")
    return txt


# ---------- 实习僧结构 ----------
h = (RAW / "shixiseng_search.html").read_text(encoding="utf-8")
i = h.find("intern-detail")
print("--- shixiseng around intern-detail ---")
print(unescape(h[max(0, i - 2000):i + 800])[:2600])
print("\n--- __NUXT__ head ---")
j = h.find("__NUXT__")
print(h[j:j + 1200])
