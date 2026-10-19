# -*- coding: utf-8 -*-
"""需求解析：关键词统计、岗位族画像、技能分层、具名工具提及率。"""
import re, json, pathlib
import pandas as pd
import numpy as np
import lexicon

DATA = pathlib.Path("data")
df = pd.read_csv(DATA / "jobs_1000.csv")
N = len(df)
df["jd_all"] = (df["岗位名称"].fillna("") + "\n" + df["JD全文"].fillna(""))
df["req_all"] = df["任职要求"].fillna("")
df["resp_all"] = df["岗位职责"].fillna("")

PATS = [(c, cat, re.compile("|".join(p), re.I)) for c, cat, p in lexicon.TERMS]
rows = []
for canon, cat, pat in PATS:
    m_all = df["jd_all"].map(lambda t: bool(pat.search(t)))
    m_title = df["岗位名称"].map(lambda t: bool(pat.search(str(t))))
    m_req = df["req_all"].map(lambda t: bool(pat.search(str(t))))
    m_resp = df["resp_all"].map(lambda t: bool(pat.search(str(t))))
    cnt = int(m_all.sum())
    if cnt == 0:
        continue
    by_arch = df[m_all]["archetype"].value_counts()
    total_by_arch = df["archetype"].value_counts()
    lift = {}
    for a in total_by_arch.index:
        p_term = cnt / N
        p_in = (by_arch.get(a, 0) / total_by_arch[a]) if total_by_arch[a] else 0
        lift[a] = round(p_in / p_term, 2) if p_term else 0
    top_lift = sorted(lift.items(), key=lambda x: -x[1])[:3]
    rows.append(dict(
        term=canon, category=cat, doc_count=cnt, share=round(cnt / N * 100, 1),
        title_count=int(m_title.sum()), title_share=round(m_title.sum() / N * 100, 1),
        in_requirements=round(m_req.sum() / N * 100, 1),
        in_responsibilities=round(m_resp.sum() / N * 100, 1),
        top_archetype_lift=" / ".join(f"{a}({v}x)" for a, v in top_lift if v > 1),
    ))

kw = pd.DataFrame(rows).sort_values(["doc_count", "share"], ascending=False).reset_index(drop=True)
kw["rank"] = kw.index + 1
kw.to_csv(DATA / "keywords.csv", index=False, encoding="utf-8-sig")
print("keywords:", len(kw))
print(kw.head(30)[["rank", "term", "category", "doc_count", "share", "title_share"]].to_string(index=False))

# ---------- 技能分层 ----------
must = kw[(kw.share >= 25)].copy()
plus = kw[(kw.share >= 8) & (kw.share < 25)].copy()
diff = kw[(kw.share >= 2) & (kw.share < 8)].copy()
layers = []
for name, sub in [("必备(≥25% JD)", must), ("加分(8-25%)", plus), ("差异化(2-8%)", diff)]:
    for _, r in sub.iterrows():
        layers.append(dict(layer=name, term=r["term"], category=r["category"],
                           share=r["share"], doc_count=r["doc_count"]))
pd.DataFrame(layers).to_csv(DATA / "skill_layers.csv", index=False, encoding="utf-8-sig")

# ---------- 岗位族画像 ----------
arch_rows = []
for a, g in df.groupby("archetype"):
    sub = g["jd_all"]
    terms = []
    for canon, cat, pat in PATS:
        c = int(sub.map(lambda t: bool(pat.search(str(t)))).sum())
        if c / len(g) >= 0.15:
            terms.append((canon, round(c / len(g) * 100, 0)))
    terms = sorted(terms, key=lambda x: -x[1])[:14]
    city = g["城市"].fillna("").str.split(",").explode().str.strip()
    city = city[city != ""].value_counts().head(5)
    sal = g["年薪(万)"].dropna()
    arch_rows.append(dict(
        archetype=a, count=len(g), share=round(len(g) / N * 100, 1),
        avg_rel=round(g["相关性分"].mean(), 1),
        salary_median=round(float(sal.median()), 1) if len(sal) else "",
        typical_titles=" | ".join(g["岗位名称"].head(5).tolist()),
        top_cities=" / ".join(f"{k}:{v}" for k, v in city.items()),
        top_companies=" / ".join(g["公司"].value_counts().head(6).index.tolist()),
        top_terms=" | ".join(f"{t}({s}%)" for t, s in terms),
    ))
arch = pd.DataFrame(arch_rows).sort_values("count", ascending=False)
arch.to_csv(DATA / "archetypes.csv", index=False, encoding="utf-8-sig")
print("\narchetypes saved")
print(arch[["archetype", "count", "share", "salary_median"]].to_string(index=False))

# ---------- 词 × 岗位族 矩阵 ----------
top_terms = kw.head(45)["term"].tolist()
mat = {}
for canon, cat, pat in PATS:
    if canon not in top_terms:
        continue
    row = {}
    for a, g in df.groupby("archetype"):
        c = int(g["jd_all"].map(lambda t: bool(pat.search(str(t)))).sum())
        row[a] = round(c / len(g) * 100, 1)
    mat[canon] = row
pd.DataFrame(mat).T.to_csv(DATA / "keyword_archetype_matrix.csv", encoding="utf-8-sig")

# ---------- 具名工具 / 框架提及率 ----------
TOOLS = [
    ("LangChain", r"LangChain"), ("LangGraph", r"LangGraph"), ("LlamaIndex", r"Llama\s*Index|LlamaIndex"),
    ("AutoGen", r"AutoGen"), ("CrewAI", r"CrewAI"), ("Semantic Kernel", r"Semantic\s*Kernel"),
    ("Dify", r"Dify"), ("Coze/扣子", r"Coze|扣子"), ("n8n", r"n8n"), ("Flowise", r"Flowise"),
    ("RAGFlow", r"RAGFlow"), ("FastGPT", r"FastGPT"), ("QAnything", r"QAnything"),
    ("Milvus", r"Milvus"), ("Faiss", r"Faiss"), ("Qdrant", r"Qdrant"), ("Elasticsearch", r"Elasticsearch|Elastic\s*Search|\bES\b"),
    ("pgvector", r"pgvector"), ("向量数据库(泛称)", r"向量数据库|Vector\s*DB"),
    ("vLLM", r"vLLM"), ("SGLang", r"SGLang"), ("LMDeploy", r"LMDeploy"), ("TensorRT", r"TensorRT"),
    ("Ollama", r"Ollama"), ("llama.cpp", r"llama\.cpp"),
    ("HuggingFace/Transformers", r"Hugging\s*Face|Transformers"),
    ("PEFT/LoRA", r"PEFT|LoRA"), ("LLaMA-Factory", r"LLaMA-?Factory"), ("Unsloth", r"Unsloth"),
    ("TRL/RLHF", r"\bTRL\b|RLHF"), ("DeepSpeed", r"DeepSpeed"), ("Megatron", r"Megatron"),
    ("MCP", r"\bMCP\b"), ("A2A", r"\bA2A\b"), ("Function Calling", r"Function\s*Call|工具调用"),
    ("OpenAI", r"OpenAI|GPT-?[45]"), ("Claude", r"Claude"), ("Qwen/通义", r"Qwen|通义"),
    ("DeepSeek", r"DeepSeek"), ("GLM/智谱", r"GLM|智谱"), ("Kimi/月之暗面", r"Kimi|月之暗面"),
    ("豆包/火山", r"豆包|火山引擎"), ("文心/百度", r"文心|千帆"), ("混元/腾讯", r"混元"),
    ("LangSmith/LangFuse", r"LangSmith|LangFuse|Langfuse"), ("DSPy", r"DSPy"),
    ("Ollama", r"Ollama"), ("Kubernetes", r"Kubernetes|\bK8s\b"), ("Docker", r"Docker"),
]
trows = []
for name, pat in TOOLS:
    p = re.compile(pat, re.I)
    c = int(df["jd_all"].map(lambda t: bool(p.search(str(t)))).sum())
    trows.append(dict(tool=name, doc_count=c, share=round(c / N * 100, 1)))
tools = pd.DataFrame(trows).drop_duplicates("tool").sort_values("doc_count", ascending=False)
tools.to_csv(DATA / "tools_mentions.csv", index=False, encoding="utf-8-sig")
print("\ntools top20:\n", tools.head(20).to_string(index=False))

# ---------- 基础分布 ----------
def dist(col):
    s = df[col].fillna("").astype(str)
    return s.replace("", "未知").value_counts()

city = df["城市"].fillna("").str.split(",").explode().str.strip()
city = city[city != ""].value_counts().head(15)
print("\n城市 top15:\n", city.to_string())
print("\n学历:\n", dist("学历要求").head(8).to_string())
print("\n薪资(万)::", df["年薪(万)"].describe().round(1).to_dict())
print("\n届别:\n", dist("届别").head(6).to_string())

summary = dict(
    total=N,
    companies=int(df["公司"].nunique()),
    cities=int(city.shape[0]),
    sources=dist("数据来源").to_dict(),
    tiers=dist("样本层级").to_dict(),
    grad=dist("届别").head(5).to_dict(),
    edu=dist("学历要求").head(6).to_dict(),
    salary=df["年薪(万)"].describe().round(1).to_dict(),
    cities_top=city.to_dict(),
    updated="2026-10-19",
)
with (DATA / "summary.json").open("w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=1, default=str)
print("\nsummary saved")
