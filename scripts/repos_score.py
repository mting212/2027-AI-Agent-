# -*- coding: utf-8 -*-
"""GitHub 项目匹配评分：含金量 / 说服力 / 可上手 / 需求匹配度 -> 综合推荐分。
并用 JD 语料中的具名工具提及率、关键词覆盖率做数据驱动校准。
"""
import json, math, pathlib, re
import pandas as pd
import numpy as np

DATA = pathlib.Path("data")
raw = json.loads((DATA / "repos_raw.json").read_text(encoding="utf-8"))
kw = pd.read_csv(DATA / "keywords.csv")
tools = pd.read_csv(DATA / "tools_mentions.csv")
arch = pd.read_csv(DATA / "archetypes.csv")

kw_share = dict(zip(kw["term"], kw["share"]))
tool_share = dict(zip(tools["tool"], tools["share"]))
matdf = pd.read_csv(DATA / "keyword_archetype_matrix.csv", index_col=0)
MAT = {t: {a: float(v) for a, v in row.dropna().items()} for t, row in matdf.iterrows()}

# 项目 -> 语料中具名工具（用于说服力校准）
TOOLMAP = {
    "langchain-ai/langchain": "LangChain", "langchain-ai/langgraph": "LangGraph",
    "run-llama/llama_index": "LlamaIndex", "microsoft/autogen": "AutoGen",
    "crewAIInc/crewAI": "CrewAI", "microsoft/semantic-kernel": "Semantic Kernel",
    "langgenius/dify": "Dify", "FlowiseAI/Flowise": "Flowise",
    "infiniflow/ragflow": "RAGFlow", "labring/FastGPT": "FastGPT",
    "netease-youdao/QAnything": "QAnything", "milvus-io/milvus": "Milvus",
    "facebookresearch/faiss": "Faiss", "qdrant/qdrant": "Qdrant",
    "vllm-project/vllm": "vLLM", "sgl-project/sglang": "SGLang",
    "InternLM/lmdeploy": "LMDeploy", "NVIDIA/TensorRT-LLM": "TensorRT",
    "ollama/ollama": "Ollama", "ggml-org/llama.cpp": "llama.cpp",
    "hiyouga/LLaMA-Factory": "LLaMA-Factory", "unslothai/unsloth": "Unsloth",
    "huggingface/peft": "PEFT/LoRA", "huggingface/trl": "TRL/RLHF",
    "modelcontextprotocol/servers": "MCP", "modelcontextprotocol/python-sdk": "MCP",
    "QwenLM/Qwen-Agent": "Qwen/通义", "QwenLM/Qwen3": "Qwen/通义",
    "deepseek-ai/DeepSeek-V3": "DeepSeek", "zai-org/GLM-4": "GLM/智谱",
    "langfuse/langfuse": "LangSmith/LangFuse", "n8n-io/n8n": "n8n",
    "Arize-ai/phoenix": "LangSmith/LangFuse",
}

CLUSTER_ARCH = {
    "Agent框架与编排": ["Agent应用开发", "Agent算法/研究"],
    "MCP生态": ["Agent应用开发"],
    "RAG与知识库": ["RAG/知识库工程", "Agent应用开发"],
    "Agent应用与产品": ["AI产品经理/产品", "Agent应用开发"],
    "代码智能体": ["Agent应用开发"],
    "浏览器与ComputerUse": ["Agent应用开发"],
    "记忆与上下文": ["Agent应用开发", "Agent算法/研究"],
    "训练与微调": ["大模型训练/微调", "Agent算法/研究"],
    "推理与部署": ["AI Infra/推理部署"],
    "评测与可观测": ["AI测试/评测", "RAG/知识库工程"],
    "多模态与语音": ["多模态/具身"],
    "安全与护栏": ["Agent安全"],
    "大模型与生态": ["Agent算法/研究", "大模型训练/微调"],
    "学习路线与教程": ["Agent应用开发", "Agent算法/研究", "RAG/知识库工程"],
}

NOW = pd.Timestamp("2026-10-19")


def days_since(s):
    try:
        return (NOW - pd.Timestamp(s[:10])).days
    except Exception:
        return 999


rows = []
for r in raw:
    if not r.get("ok"):
        continue
    stars = r.get("stars") or 0
    forks = r.get("forks") or 0
    days = days_since(r.get("pushed") or "")
    archived = bool(r.get("archived"))

    # ---- 含金量 ----
    star_s = min(100, max(0, 100 * (math.log10(stars + 1) / math.log10(200000))))
    act_s = 100 if days <= 30 else 85 if days <= 90 else 65 if days <= 180 else 45 if days <= 365 else 20
    eco_s = min(100, (forks / max(stars, 1)) * 260)
    lic_s = 90 if (r.get("license") in ("Apache-2.0", "MIT", "BSD-3-Clause", "MPL-2.0")) else \
            60 if r.get("license") else 40
    gold = 0.42 * star_s + 0.28 * act_s + 0.15 * eco_s + 0.15 * lic_s
    if archived:
        gold *= 0.55

    # ---- 需求匹配度（按目标岗位族的 JD 关键词占比，而非全语料均值）----
    terms = r.get("jd_terms") or []
    target_arch = CLUSTER_ARCH.get(r.get("cluster"), [])
    vals = []
    for t in terms:
        if t in MAT and target_arch:
            vals.append(max(MAT[t].get(a, 0) for a in target_arch))
    cov = float(np.mean(vals)) if vals else 0.0                            # 0~100（族内占比）
    tool = TOOLMAP.get(r["full_name"], "")
    tm = tool_share.get(tool, 0)                                            # 0~43
    match = min(100, cov * 0.85 + tm * 0.9)

    # ---- 说服力 ----
    pers = r.get("persuasion", 3)
    persuasion = 0.45 * (pers / 5 * 100) + 0.30 * min(100, cov * 0.9) + 0.25 * min(100, tm * 2.2)
    if r.get("archived"):
        persuasion *= 0.6

    # ---- 可上手 ----
    diff = r.get("difficulty", 3)
    hours = r.get("hours", 6)
    hands = (6 - diff) / 5 * 50 + max(0, 1 - hours / 16) * 25 + (15 if r.get("zh_docs") else 4) \
            + (10 if not r.get("gpu_required") else 0)
    hands = min(100, max(0, hands))

    final = 0.32 * gold + 0.32 * persuasion + 0.18 * hands + 0.18 * match
    grade = "S" if final >= 80 else "A" if final >= 72 else "B" if final >= 64 else "C" if final >= 56 else "D"

    rows.append(dict(
        full_name=r["full_name"], url=r.get("url"), cluster=r.get("cluster"),
        stars=stars, forks=forks, pushed=r.get("pushed", "")[:10], days_since_push=days,
        license=r.get("license"), language=r.get("language"), archived=bool(r.get("archived")),
        difficulty=diff, hours=hours, gpu_required=bool(r.get("gpu_required")),
        zh_docs=bool(r.get("zh_docs")),
        jd_term_coverage=round(cov, 1), tool_mention_share=tm,
        score_gold=round(gold, 1), score_persuasion=round(persuasion, 1),
        score_hands_on=round(hands, 1), score_match=round(match, 1),
        score_total=round(final, 1), grade=grade,
        jd_terms=" / ".join(terms), matched_archetypes=" / ".join(CLUSTER_ARCH.get(r.get("cluster"), [])),
        why=r.get("why"), task=r.get("task"), deliverable=r.get("output"),
        interview=r.get("interview"), description=(r.get("description") or "")[:180],
        topics=", ".join((r.get("topics") or [])[:6]),
    ))

df = pd.DataFrame(rows).sort_values("score_total", ascending=False)
df["rank"] = range(1, len(df) + 1)
LEARN = {"学习路线与教程"}
INFRA = {"训练与微调", "推理与部署", "评测与可观测", "安全与护栏", "大模型与生态"}
df["project_type"] = df["cluster"].map(
    lambda c: "学习型(打基础)" if c in LEARN else ("基础设施型(硬核加分)" if c in INFRA else "作品型(可演示/可写简历)"))
df.to_csv(DATA / "projects.csv", index=False, encoding="utf-8-sig")
print("projects:", len(df))
print(df.head(25)[["rank", "full_name", "cluster", "stars", "score_gold", "score_persuasion",
                   "score_hands_on", "score_match", "score_total", "grade"]].to_string(index=False))
print("\ngrade dist:", df["grade"].value_counts().to_dict())
print("\ncluster avg:", df.groupby("cluster")["score_total"].mean().round(1).sort_values(ascending=False).to_dict())

# ---------- 岗位族 → 项目组合 ----------
ARCH_CLUSTERS = {
    "Agent应用开发": ["Agent框架与编排", "Agent应用与产品", "MCP生态", "代码智能体", "浏览器与ComputerUse"],
    "Agent算法/研究": ["训练与微调", "大模型与生态", "Agent框架与编排"],
    "RAG/知识库工程": ["RAG与知识库", "评测与可观测"],
    "AI Infra/推理部署": ["推理与部署"],
    "AI产品经理/产品": ["Agent应用与产品", "学习路线与教程"],
    "多模态/具身": ["多模态与语音"],
    "Agent安全": ["安全与护栏"],
    "大模型训练/微调": ["训练与微调", "大模型与生态"],
    "AI测试/评测": ["评测与可观测", "安全与护栏"],
    "全栈/前端AI应用": ["Agent应用与产品", "Agent框架与编排"],
    "其他Agent相关": ["Agent框架与编排", "Agent应用与产品"],
    "AI解决方案/交付": ["Agent应用与产品", "Agent框架与编排"],
}
arch_counts = dict(zip(arch["archetype"], arch["count"]))
plan = []
for a, cnt in arch_counts.items():
    clusters = ARCH_CLUSTERS.get(a, ["Agent框架与编排"])
    cand = df[df["cluster"].isin(clusters)]
    nonlearn = cand[cand["project_type"] != "学习型(打基础)"]
    if len(nonlearn) >= 3:
        cand = nonlearn
    if cand.empty:
        cand = df
    good = cand[cand["grade"].isin(["S", "A", "B"])]
    base = good if len(good) >= 3 else cand
    core = base[base["grade"].isin(["S", "A"])].sort_values("score_total", ascending=False).head(1)
    if core.empty:
        core = base.sort_values("score_total", ascending=False).head(1)
    used = set(core["full_name"])
    fast = base[~base["full_name"].isin(used)].sort_values(
        ["hours", "score_total"], ascending=[True, False]).head(1)
    used |= set(fast["full_name"])
    hard = base[~base["full_name"].isin(used)].sort_values(
        ["difficulty", "score_total"], ascending=[False, False]).head(1)
    pick = []
    for tag, sub in [("核心作品", core), ("速成作品", fast), ("硬核加分", hard)]:
        if not sub.empty:
            rr = sub.iloc[0]
            pick.append(f"{tag}：{rr['full_name']}（{rr['hours']}h, 难度{rr['difficulty']}/5, {rr['grade']}级）")
    plan.append(dict(archetype=a, jd_count=cnt, share=round(cnt / 1000 * 100, 1),
                     projects=" ｜ ".join(pick)))
pd.DataFrame(plan).sort_values("jd_count", ascending=False).to_csv(
    DATA / "archetype_project_plan.csv", index=False, encoding="utf-8-sig")
print("\nplan saved")
