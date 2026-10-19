# -*- coding: utf-8 -*-
"""测绘牛客网岗位搜索 API：schema、recruitType、pageSize、关键词总量。"""
import subprocess, json, time, collections

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
URL = "https://www.nowcoder.com/np-api/u/job/search"


def search(**kw):
    body = {"query": "Agent", "page": 1, "pageSize": 10, "recruitType": 1,
            "order": 0, "type": 0, "city": 0}
    body.update(kw)
    p = subprocess.run(["curl.exe", "-s", "-L", "--compressed", "--max-time", "25", "-A", UA,
                        "-H", "Referer: https://www.nowcoder.com/jobs/fulltime/center",
                        "-H", "Origin: https://www.nowcoder.com",
                        "-H", "Content-Type: application/json;charset=UTF-8",
                        "-X", "POST", "--data", json.dumps(body, ensure_ascii=False), URL],
                       capture_output=True)
    t = p.stdout.decode("utf-8", "replace")
    try:
        return json.loads(t), None
    except Exception:
        return None, t[:300]


j, err = search()
print("totals:", {k: j["data"][k] for k in j["data"] if k != "datas"})
rec = j["data"]["datas"][0]
print("\nrecord keys:", list(rec.keys()))
print(json.dumps({k: v for k, v in rec.items() if k != "ext"}, ensure_ascii=False, indent=1)[:1500])
print("\next:", rec.get("ext", "")[:400])

print("\n### recruitType 取值")
for rt in [0, 1, 2, 3, 4]:
    jj, e = search(recruitType=rt, pageSize=1)
    print(f"  recruitType={rt} total={(jj or {}).get('data',{}).get('totalCount')} err={e}")
    time.sleep(0.7)

print("\n### pageSize 上限")
for ps in [10, 20, 50, 100]:
    jj, e = search(pageSize=ps)
    print(f"  pageSize={ps} returned={len((jj or {}).get('data',{}).get('datas') or [])} err={e}")
    time.sleep(0.7)

print("\n### 关键词总量 (recruitType=1)")
for q in ["Agent", "AI Agent", "智能体", "大模型", "LLM", "RAG", "AI应用", "AI开发",
          "提示词", "Prompt", "多智能体", "工作流", "MCP", "算法", "NLP", "大语言模型",
          "AIGC", "AI产品", "知识库", "检索增强", "Agent开发", "AI工程师"]:
    jj, e = search(query=q, pageSize=1)
    print(f"  {q!r:16} total={(jj or {}).get('data',{}).get('totalCount')}")
    time.sleep(0.7)
