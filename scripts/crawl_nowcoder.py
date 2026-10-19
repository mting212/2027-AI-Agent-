# -*- coding: utf-8 -*-
"""牛客网岗位搜索采集器：多关键词 × 全分页，落 raw/nowcoder_raw.jsonl（按 id 去重）。"""
import subprocess, json, time, pathlib, sys

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
URL = "https://www.nowcoder.com/np-api/u/job/search"
RAW = pathlib.Path("raw")
RAW.mkdir(exist_ok=True)
OUT = RAW / "nowcoder_raw.jsonl"

TERMS = [
    "Agent", "AI Agent", "Agent开发", "Agentic", "智能体", "多智能体",
    "大模型", "LLM", "大语言模型", "RAG", "检索增强", "AI应用", "AI开发",
    "AI工程师", "AIGC", "生成式AI", "AI产品", "AI产品经理", "AI解决方案",
    "提示词", "Prompt", "知识库", "向量数据库", "MCP", "Function Calling",
    "工具调用", "工作流", "代码生成", "Coding Agent", "智能客服", "数字人",
    "AI Infra", "推理优化", "模型微调", "强化学习", "数据合成", "AI评测",
    "AI安全", "具身智能", "多模态", "语音识别", "NLP", "AI算法",
    "机器学习", "深度学习", "算法工程师", "搜索算法", "推荐算法", "AI运营",
]

PAGE_SIZE = 100
MAX_PAGES = 8
DELAY = 1.15


def post(body, retries=2):
    for i in range(retries + 1):
        p = subprocess.run(
            ["curl.exe", "-s", "-L", "--compressed", "--max-time", "30", "-A", UA,
             "-H", "Referer: https://www.nowcoder.com/jobs/fulltime/center",
             "-H", "Origin: https://www.nowcoder.com",
             "-H", "Content-Type: application/json;charset=UTF-8",
             "-X", "POST", "--data", json.dumps(body, ensure_ascii=False), URL],
            capture_output=True)
        t = p.stdout.decode("utf-8", "replace")
        try:
            j = json.loads(t)
            if j.get("code") == 0:
                return j["data"]
        except Exception:
            pass
        time.sleep(2 + i * 2)
    return None


seen = set()
if OUT.exists():
    with OUT.open(encoding="utf-8") as f:
        for line in f:
            try:
                seen.add(json.loads(line)["id"])
            except Exception:
                pass
print("resume: existing ids", len(seen), flush=True)

fout = OUT.open("a", encoding="utf-8")
total_new = 0
for term in TERMS:
    body0 = {"query": term, "page": 1, "pageSize": PAGE_SIZE, "recruitType": 0,
             "order": 0, "type": 0, "city": 0}
    d = post(body0)
    if not d:
        print(f"[FAIL] {term}", flush=True)
        continue
    pages = min(d.get("totalPage") or 1, MAX_PAGES)
    added = 0
    for page in range(1, pages + 1):
        body = dict(body0, page=page)
        dd = d if page == 1 else post(body)
        if not dd:
            break
        for rec in dd.get("datas") or []:
            rid = rec.get("id")
            if rid in seen:
                continue
            seen.add(rid)
            rec["_query"] = term
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            added += 1
        if page < pages:
            time.sleep(DELAY)
    fout.flush()
    total_new += added
    print(f"[{term}] total={d.get('totalCount')} pages={pages} new={added} "
          f"cum={len(seen)}", flush=True)
    time.sleep(DELAY)

fout.close()
print("DONE new=", total_new, "unique=", len(seen), flush=True)
