# -*- coding: utf-8 -*-
import re, json, subprocess, urllib.parse, pathlib, time

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
RAW = pathlib.Path("raw")


def curl(url, referer=None, save=None):
    cmd = ["curl.exe", "-s", "-L", "--compressed", "--max-time", "25", "-A", UA,
           "-H", "Accept-Language: zh-CN,zh;q=0.9"]
    if referer:
        cmd += ["-H", "Referer: " + referer]
    cmd.append(url)
    t = subprocess.run(cmd, capture_output=True).stdout.decode("utf-8", "replace")
    if save:
        (RAW / save).write_text(t, encoding="utf-8")
    return t


# ---------- 应届生搜索页 ----------
t = curl("https://q.yingjiesheng.com/jobs/search/?keyword=AI%20Agent", save="q_yjs.html")
print("q.yjs len", len(t), "|", t[:200].replace("\n", " "))
js = sorted(set(re.findall(r'src="([^"]+\.js)"', t)))
print("js:", js[:10])
apis = sorted(set(re.findall(r'["\'](/[a-z0-9]+/[A-Za-z0-9_/\-]*(?:search|list|job)[A-Za-z0-9_/\-]*)["\']', t)))
print("api hints:", apis[:15])
for u in ["https://q.yingjiesheng.com/api/job/search?keyword=Agent&page=1&pageSize=10",
          "https://q.yingjiesheng.com/pc/searchintention"]:
    time.sleep(0.6)
    r = curl(u, referer="https://q.yingjiesheng.com/jobs/search/")
    print("  ->", u, len(r), r[:150].replace("\n", " "))

# 从 JS bundle 里挖 API 路径
for jsu in js[:4]:
    if not jsu.startswith("http"):
        jsu = urllib.parse.urljoin("https://q.yingjiesheng.com/jobs/search/", jsu)
    time.sleep(0.6)
    body = curl(jsu)
    found = sorted(set(re.findall(r'["\'](/[A-Za-z0-9_/\-]{4,50})["\']', body)))
    hits = [f for f in found if any(k in f.lower() for k in ("job", "search", "list", "position"))]
    print("bundle", jsu.split("/")[-1], "len", len(body), "hits:", hits[:12])

# ---------- 牛客 ----------
t = curl("https://www.nowcoder.com/jobs/fulltime/center", save="nc.html")
print("\nnowcoder len", len(t))
js = sorted(set(re.findall(r'src="([^"]+\.js)"', t)))
print("js count", len(js), js[:5])
for jsu in js[:6]:
    if not jsu.startswith("http"):
        jsu = urllib.parse.urljoin("https://www.nowcoder.com/", jsu)
    time.sleep(0.5)
    body = curl(jsu, referer="https://www.nowcoder.com/jobs/fulltime/center")
    hits = sorted(set(re.findall(r'["\'](/api/[A-Za-z0-9_/\-]{4,60})["\']', body)))
    if hits:
        print("  bundle", jsu.split("/")[-1][:40], "->", hits[:14])
