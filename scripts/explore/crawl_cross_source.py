# -*- coding: utf-8 -*-
"""跨源补充采集：腾讯 / 百度 / 美团，落 raw/*_raw.jsonl。低频（≥1.1s/req）。"""
import subprocess, json, time, pathlib, urllib.parse

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
RAW = pathlib.Path("raw")
RAW.mkdir(exist_ok=True)
DELAY = 1.15


def curl(url, post=None, form=None, referer=None, retries=2):
    for i in range(retries + 1):
        cmd = ["curl.exe", "-s", "-L", "--compressed", "--max-time", "30", "-A", UA,
               "-H", "Accept-Language: zh-CN,zh;q=0.9"]
        if referer:
            cmd += ["-H", "Referer: " + referer]
        if post is not None:
            cmd += ["-X", "POST", "-H", "Content-Type: application/json;charset=UTF-8",
                    "--data", json.dumps(post, ensure_ascii=False)]
        if form is not None:
            cmd += ["-X", "POST", "-H", "Content-Type: application/x-www-form-urlencoded",
                    "--data", urllib.parse.urlencode(form)]
        cmd.append(url)
        t = subprocess.run(cmd, capture_output=True).stdout.decode("utf-8", "replace")
        if t.strip():
            return t
        time.sleep(2 + i * 2)
    return ""


def write(path, rec):
    with pathlib.Path(path).open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ---------------- 腾讯 ----------------
TENCENT_KW = ["Agent", "大模型", "LLM", "智能体", "AI", "算法", "RAG", "多模态",
              "NLP", "AI应用", "生成式", "推理优化"]
out = RAW / "tencent_raw.jsonl"
seen = set()
if out.exists():
    for line in out.open(encoding="utf-8"):
        try:
            seen.add(json.loads(line)["PostId"])
        except Exception:
            pass
print("tencent resume", len(seen), flush=True)
for kw in TENCENT_KW:
    page, added = 1, 0
    while page <= 6:
        url = ("https://careers.tencent.com/tencentcareer/api/post/Query?timestamp=1700000000000"
               f"&keyword={urllib.parse.quote(kw)}&pageIndex={page}&pageSize=100"
               "&language=zh-cn&area=cn&countryId=&cityId=&bgIds=&productId="
               "&categoryId=&parentCategoryId=&attrId=")
        t = curl(url, referer="https://careers.tencent.com/")
        try:
            j = json.loads(t)
            posts = j["Data"]["Posts"]
            total = j["Data"]["Count"]
        except Exception:
            print("tencent fail", kw, page, t[:120], flush=True)
            break
        if not posts:
            break
        for p in posts:
            pid = p.get("PostId")
            if pid in seen:
                continue
            seen.add(pid)
            p["_query"] = kw
            write(out, p)
            added += 1
        if page * 100 >= total:
            break
        page += 1
        time.sleep(DELAY)
    print(f"[tencent] {kw} added={added} cum={len(seen)}", flush=True)
    time.sleep(DELAY)

# ---------------- 百度 ----------------
BD_KW = ["Agent", "大模型", "智能体", "AI", "LLM", "算法", "RAG", "多模态", "NLP"]
out = RAW / "baidu_raw.jsonl"
seen = set()
if out.exists():
    for line in out.open(encoding="utf-8"):
        try:
            seen.add(json.loads(line)["postId"])
        except Exception:
            pass
print("baidu resume", len(seen), flush=True)
for rt in ["校招", "INTERN", "SOCIAL"]:
    for kw in BD_KW:
        page, added = 1, 0
        while page <= 5:
            t = curl("https://talent.baidu.com/httservice/getPostListNew",
                     form={"recruitType": rt, "pageSize": 100, "keyWord": kw,
                           "curPage": page, "projectType": "", "postType": "",
                           "workPlace": "", "bg": ""},
                     referer="https://talent.baidu.com/jobs/list")
            try:
                j = json.loads(t)
                lst = (j.get("data") or {}).get("list") or []
                total = int((j.get("data") or {}).get("total") or 0)
            except Exception:
                print("baidu fail", rt, kw, page, t[:120], flush=True)
                break
            if not lst:
                break
            for p in lst:
                pid = p.get("postId")
                if pid in seen:
                    continue
                seen.add(pid)
                p["_query"] = kw
                p["_recruit_type"] = rt
                write(out, p)
                added += 1
            if page * 100 >= total:
                break
            page += 1
            time.sleep(DELAY)
        print(f"[baidu] {rt} {kw} added={added} cum={len(seen)}", flush=True)
        time.sleep(DELAY)

# ---------------- 美团 ----------------
MT = "https://zhaopin.meituan.com/api/official/job/getJobList"
MTREF = "https://zhaopin.meituan.com/web/position"
MT_KW = ["Agent", "大模型", "智能体", "AI", "算法", "LLM", "RAG", "多模态"]
out = RAW / "meituan_raw.jsonl"
seen = set()
if out.exists():
    for line in out.open(encoding="utf-8"):
        try:
            seen.add(json.loads(line)["jobUnionId"])
        except Exception:
            pass
print("meituan resume", len(seen), flush=True)
for kw in MT_KW:
    page, added = 1, 0
    while page <= 15:
        t = curl(MT, post={"pageNo": page, "pageSize": 20, "keyword": kw}, referer=MTREF)
        try:
            lst = (json.loads(t).get("data") or {}).get("list") or []
        except Exception:
            print("meituan fail", kw, page, t[:120], flush=True)
            break
        if not lst:
            break
        for p in lst:
            jid = p.get("jobUnionId")
            if jid in seen:
                continue
            seen.add(jid)
            p["_query"] = kw
            write(out, p)
            added += 1
        page += 1
        time.sleep(DELAY)
    print(f"[meituan] {kw} added={added} cum={len(seen)}", flush=True)
    time.sleep(DELAY)

print("DONE cross-source", flush=True)
