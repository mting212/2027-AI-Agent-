# -*- coding: utf-8 -*-
import re, subprocess, pathlib, urllib.parse

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
RAW = pathlib.Path("raw")
RAW.mkdir(exist_ok=True)


def curl(url, save=None):
    t = subprocess.run(["curl.exe", "-s", "-L", "--compressed", "--max-time", "30",
                        "-A", UA, url], capture_output=True).stdout.decode("utf-8", "replace")
    if save:
        (RAW / save).write_text(t, encoding="utf-8")
    return t


base = "https://static.nowcoder.com/nowpick/web/nowcoder/3.2.696/javascripts-wp-c/"
for f in ["lib/common.js", "page/jobHome/main.entry.js"]:
    t = curl(base + f, save=f.replace("/", "_"))
    print("###", f, len(t))
    # 所有含 job 的短字符串
    cands = sorted(set(re.findall(r'["\'`]([^"\'`]{2,80})["\'`]', t)))
    hits = [c for c in cands if "job" in c.lower() and ("/" in c or "job" == c.lower()[:3])]
    for h in hits[:60]:
        print("   ", h)
    print()
