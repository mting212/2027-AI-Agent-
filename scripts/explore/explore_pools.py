# -*- coding: utf-8 -*-
"""测绘美团 / 百度 校招岗位池规模与参数。"""
import json, subprocess, urllib.parse, time, collections

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def curl(url, post=None, form=None, referer=None):
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
    return subprocess.run(cmd, capture_output=True).stdout.decode("utf-8", "replace")


MT = "https://zhaopin.meituan.com/api/official/job/getJobList"
MTREF = "https://zhaopin.meituan.com/web/position"


def mt(**kw):
    body = {"pageNo": 1, "pageSize": 10, "keyword": "Agent"}
    body.update(kw)
    t = curl(MT, post=body, referer=MTREF)
    try:
        j = json.loads(t)
    except Exception:
        return None, t[:200]
    d = j.get("data") or {}
    return d, None


print("### 美团 空关键词 pageSize=100")
d, err = mt(keyword="", pageSize=100)
if err:
    print("ERR", err)
else:
    print("total:", d.get("total"), "returned:", len(d.get("list") or []))
    projs = collections.Counter((x.get("projectName") or "null") for x in d["list"])
    print("projectName dist:", projs.most_common(12))
    print("jobType dist:", collections.Counter(x.get("jobType") for x in d["list"]))
    print("sample names:", [x.get("name") for x in d["list"][:15]])

print("\n### 美团 关键词总量")
for kw in ["Agent", "大模型", "智能体", "AI", "算法", "LLM", "RAG", ""]:
    time.sleep(1)
    d, err = mt(keyword=kw, pageSize=1)
    print(f"  {kw!r:10} total={(d or {}).get('total')} err={err}")

print("\n### 美团 pageSize 上限")
for ps in [20, 50, 100, 200]:
    time.sleep(1)
    d, err = mt(keyword="", pageSize=ps)
    print(f"  pageSize={ps} returned={len((d or {}).get('list') or [])} err={err}")

print("\n### 美团 2027届秋招 project 过滤尝试")
for body in [{"projectId": 115}, {"projectName": "2026年（2027届）秋季校招"},
             {"jobType": "1", "pageSize": 100}]:
    time.sleep(1)
    b = {"pageNo": 1, "pageSize": 10, "keyword": ""}
    b.update(body)
    t = curl(MT, post=b, referer=MTREF)
    try:
        d = json.loads(t).get("data") or {}
        projs = collections.Counter((x.get("projectName") or "null") for x in (d.get("list") or []))
        print("  body", body, "-> total", d.get("total"), projs.most_common(4))
    except Exception:
        print("  body", body, "ERR", t[:160])

print("\n### 百度 校招/实习/社招 关键词总量")
BD = "https://talent.baidu.com/httservice/getPostListNew"
for rt in ["校招", "INTERN", "SOCIAL"]:
    for kw in ["Agent", "大模型", "智能体", "AI", "LLM", "算法"]:
        time.sleep(0.8)
        t = curl(BD, form={"recruitType": rt, "pageSize": 1, "keyWord": kw, "curPage": 1,
                           "projectType": "", "postType": "", "workPlace": "", "bg": ""},
                 referer="https://talent.baidu.com/jobs/list")
        try:
            j = json.loads(t)
            print(f"  {rt:7} {kw:6} total={(j.get('data') or {}).get('total')}")
        except Exception:
            print(f"  {rt:7} {kw:6} ERR {t[:100]}")
