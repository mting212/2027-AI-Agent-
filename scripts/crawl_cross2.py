# -*- coding: utf-8 -*-
"""百度(20/页) + 美团(20/页, 校招记录补详情) 采集。"""
import subprocess, json, time, pathlib, urllib.parse

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
RAW = pathlib.Path("raw")
DELAY = 1.1


def curl(url, post=None, form=None, referer=None):
    cmd = ["curl.exe", "-s", "-L", "--compressed", "--max-time", "15", "-A", UA,
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
    return subprocess.run(cmd, capture_output=True).stdout.decode("utf-8", "replace")


out = RAW / "baidu_raw.jsonl"
seen = set()
if out.exists():
    for line in out.open(encoding="utf-8"):
        try:
            seen.add(json.loads(line)["postId"])
        except Exception:
            pass
print("baidu resume", len(seen), flush=True)
BD_KW = ["Agent", "大模型", "智能体", "AI", "LLM", "算法", "RAG", "多模态", "NLP", "AI应用"]
for rt in ["校招", "INTERN", "SOCIAL"]:
    for kw in BD_KW:
        added, page = 0, 1
        while page <= 12:
            t = curl("https://talent.baidu.com/httservice/getPostListNew",
                     form={"recruitType": rt, "pageSize": 20, "keyWord": kw,
                           "curPage": page, "projectType": "", "postType": "",
                           "workPlace": "", "bg": ""},
                     referer="https://talent.baidu.com/jobs/list")
            try:
                j = json.loads(t)
                if j.get("status") != "ok":
                    break
                lst = (j.get("data") or {}).get("list") or []
                total = int((j.get("data") or {}).get("total") or 0)
            except Exception:
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
                with out.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(p, ensure_ascii=False) + "\n")
                added += 1
            if page * 20 >= total:
                break
            page += 1
            time.sleep(DELAY)
        print(f"[baidu] {rt} {kw} added={added} cum={len(seen)}", flush=True)
        time.sleep(DELAY)

# ---------------- 美团 ----------------
MT = "https://zhaopin.meituan.com/api/official/job/getJobList"
MTD = "https://zhaopin.meituan.com/api/official/job/getJobDetail"
REF = "https://zhaopin.meituan.com/web/position"
out = RAW / "meituan_raw.jsonl"
seen = set()
if out.exists():
    for line in out.open(encoding="utf-8"):
        try:
            seen.add(json.loads(line)["jobUnionId"])
        except Exception:
            pass
print("meituan resume", len(seen), flush=True)
MT_KW = ["Agent", "大模型", "智能体", "AI", "算法", "LLM", "RAG", "多模态", "AI产品", "应用"]
campus = []
for kw in MT_KW:
    added, page = 0, 1
    while page <= 20:
        t = curl(MT, post={"pageNo": page, "pageSize": 20, "keyword": kw}, referer=REF)
        try:
            lst = (json.loads(t).get("data") or {}).get("list") or []
        except Exception:
            break
        if not lst:
            break
        for p in lst:
            jid = p.get("jobUnionId")
            if jid in seen:
                continue
            seen.add(jid)
            p["_query"] = kw
            with out.open("a", encoding="utf-8") as f:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")
            if str(p.get("jobType")) == "1":
                campus.append(jid)
            added += 1
        page += 1
        time.sleep(DELAY)
    print(f"[meituan] {kw} added={added} cum={len(seen)} campus={len(campus)}", flush=True)
    time.sleep(DELAY)

# 校招记录补详情（取 projectName 判定 2027 届秋招）
print("fetching meituan details for campus jobs:", len(campus), flush=True)
det_out = RAW / "meituan_detail.jsonl"
done = set()
if det_out.exists():
    for line in det_out.open(encoding="utf-8"):
        try:
            done.add(json.loads(line)["jobUnionId"])
        except Exception:
            pass
for i, jid in enumerate(campus):
    if jid in done:
        continue
    t = curl(MTD, post={"jobUnionId": jid}, referer=REF)
    try:
        d = (json.loads(t).get("data") or {})
    except Exception:
        d = {}
    with det_out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")
    if (i + 1) % 20 == 0:
        print(f"  detail {i + 1}/{len(campus)}", flush=True)
    time.sleep(DELAY)

print("DONE", flush=True)
