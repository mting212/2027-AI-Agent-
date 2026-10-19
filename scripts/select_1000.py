# -*- coding: utf-8 -*-
"""从 jobs_all.csv 中分层抽样出 1000 条「AI Agent 应用/开发」JD 语料。
分层：A-秋招/校招 > B-实习 > C-社招；公司配额 + 相关性排序。
"""
import pandas as pd
import numpy as np
import re, pathlib

DATA = pathlib.Path("data")
df = pd.read_csv(DATA / "jobs_all.csv")
df = df[~df["grad_year_eff"].isin(["2025届", "2026届", "2023届", "2028届"])].copy()
print("pool:", len(df))

df["role_domain"] = df["role_domain"].fillna("其他")
df["strong_hits"] = df["strong_hits"].fillna(0).astype(int)
df["rel_score"] = df["rel_score"].fillna(0)
df["title_hit"] = df["title_hit"].astype(bool)

# ---- 硬筛选：技术/产品/解决方案类 + Agent 强信号 ----
tech = df["role_domain"].isin(["技术研发", "产品", "其他"])
core = (df["strong_hits"] >= 2) | (df["title_hit"] & (df["strong_hits"] >= 1)) | \
       ((df["rel_score"] >= 12) & (df["strong_hits"] >= 1))
cand = df[tech & core].copy()
print("after tech+core filter:", len(cand))
print(cand["sample_tier"].value_counts().to_string())

# ---- 公司配额 ----
CAP = {"百度": 140, "腾讯": 100, "华为": 90, "快手": 45, "拼多多": 35, "字节跳动": 35,
       "美团": 40, "小米": 30, "阿里巴巴": 30, "小红书": 30, "网易": 20, "滴滴": 18,
       "哔哩哔哩": 18, "科大讯飞": 18, "携程": 15, "SHEIN希音": 15, "Shopee": 15}
DEFAULT_CAP = 8


def cap_of(c):
    return CAP.get(c, DEFAULT_CAP)


QUOTA = {"A-秋招/校招": 900, "B-实习(转正/秋招实习)": 100}

cand = cand.sort_values(["rel_score", "strong_hits", "jd_len"], ascending=False)
chosen, used = [], {}
for tier, q in QUOTA.items():
    pool = cand[cand["sample_tier"] == tier]
    picked = 0
    for _, r in pool.iterrows():
        if picked >= q:
            break
        c = r["company"]
        if used.get(c, 0) >= cap_of(c):
            continue
        used[c] = used.get(c, 0) + 1
        chosen.append(r)
        picked += 1
    print(f"{tier}: quota={q} picked={picked}")

sel = pd.DataFrame(chosen)
sel = sel.drop_duplicates("job_id")
# 不足 1000 时从剩余候选补齐（放宽公司配额）
if len(sel) < 1000:
    rest = cand[~cand["job_id"].isin(sel["job_id"]) & cand["sample_tier"].isin(list(QUOTA))]
    need = 1000 - len(sel)
    sel = pd.concat([sel, rest.head(need)], ignore_index=True)
    print("补足:", need)

# 社招样本另存（不进 1000 主集，仅作对照/画像补充）
social = cand[cand["sample_tier"] == "C-社招(画像补充)"].sort_values(
    ["rel_score", "strong_hits"], ascending=False).head(400)
social.drop_duplicates("job_id").to_csv(DATA / "jobs_social_supplement.csv", index=False, encoding="utf-8-sig")
print("social supplement:", len(social))

sel = sel.head(1000)
print("selected:", len(sel))
print(sel["sample_tier"].value_counts().to_string())
print("sources:", sel["source"].value_counts().to_dict())
print("companies:", sel["company"].nunique(), "| top:", sel["company"].value_counts().head(12).to_dict())

# 岗位族分类
ARCH = [
    ("Agent应用开发", [r"Agent", r"智能体", r"AI应用", r"AI开发", r"Agentic"],
     [r"开发", r"研发", r"工程师", r"全栈", r"后端", r"前端"]),
    ("Agent算法/研究", [r"Agent", r"智能体", r"算法", r"研究", r"大模型", r"LLM"],
     [r"算法", r"研究", r"科学家", r"实习生", r"博士"]),
    ("RAG/知识库工程", [r"RAG", r"检索增强", r"知识库", r"向量", r"检索", r"图谱"],
     [r"开发", r"工程", r"算法", r"研发"]),
    ("AI Infra/推理部署", [r"推理", r"Infra", r"部署", r"GPU", r"vLLM", r"训练框架", r"算力"],
     [r"开发", r"工程", r"算法", r"平台"]),
    ("大模型训练/微调", [r"微调", r"SFT", r"RLHF", r"预训练", r"对齐", r"训练"],
     [r"算法", r"工程", r"研究", r"开发"]),
    ("AI产品经理/产品", [r"产品"], [r"产品"]),
    ("AI解决方案/交付", [r"解决方案", r"售前", r"交付", r"实施", r"咨询"], [r"解决方案", r"售前", r"交付"]),
    ("Agent安全", [r"安全", r"护栏", r"风控", r"隐私", r"合规"], [r"安全", r"风控"]),
    ("多模态/具身", [r"多模态", r"视觉", r"语音", r"具身", r"机器人", r"数字人", r"AIGC"], [r"算法", r"工程", r"开发"]),
    ("AI测试/评测", [r"测试", r"评测", r"质量", r"Benchmark"], [r"测试", r"评测"]),
    ("AI数据工程", [r"数据工程", r"数据标注", r"数据合成", r"数据管线", r"语料"], [r"数据"]),
    ("全栈/前端AI应用", [r"前端", r"全栈", r"Web", r"小程序", r"客户端"], [r"前端", r"全栈", r"客户端"]),
]


def classify(r):
    title = str(r["title"])
    text = str(r["jd_text"])[:4000]
    best, best_score = "其他Agent相关", 0
    for name, sig, role in ARCH:
        sc = 0
        for p in sig:
            if re.search(p, title, re.I):
                sc += 3
            elif re.search(p, text, re.I):
                sc += 1
        for p in role:
            if re.search(p, title, re.I):
                sc += 2
        if sc > best_score:
            best, best_score = name, sc
    return best, best_score


cls = sel.apply(classify, axis=1)
sel["archetype"] = [c[0] for c in cls]
sel["archetype_score"] = [c[1] for c in cls]
sel["archetype"] = sel["archetype"].where(sel["archetype_score"] >= 3, "其他Agent相关")
print("\narchetype dist:\n", sel["archetype"].value_counts().to_string())

# ---- 输出字段整理 ----
def short(t, n=260):
    t = re.sub(r"\s+", " ", str(t or "")).strip()
    return t[:n]


sel["岗位职责摘要"] = sel["responsibilities"].map(lambda x: short(x, 300))
sel["任职要求摘要"] = sel["requirements"].map(lambda x: short(x, 300))
sel["匹配关键词"] = sel["rel_terms"]
sel["JD字数"] = sel["jd_len"]

cols = ["job_id", "company", "title", "archetype", "city", "sample_tier", "recruit_type",
        "grad_year_eff", "edu_req", "salary_text", "salary_wan", "source", "strong_hits",
        "rel_score", "匹配关键词", "岗位职责摘要", "任职要求摘要", "JD字数",
        "publish_date", "deadline", "url", "source_query", "project_name", "industry",
        "work_years_req", "job_family_raw", "jd_text", "responsibilities", "requirements"]
sel = sel[cols].rename(columns={
    "company": "公司", "title": "岗位名称", "city": "城市", "sample_tier": "样本层级",
    "recruit_type": "招聘类型", "grad_year_eff": "届别", "edu_req": "学历要求",
    "salary_text": "薪资", "salary_wan": "年薪(万)", "source": "数据来源",
    "strong_hits": "Agent强信号数", "rel_score": "相关性分", "publish_date": "发布时间",
    "deadline": "投递截止", "url": "原始链接", "source_query": "检索词",
    "project_name": "校招项目", "industry": "部门/行业", "work_years_req": "经验要求",
    "job_family_raw": "岗位标签", "jd_text": "JD全文", "responsibilities": "岗位职责",
    "requirements": "任职要求",
})
sel.to_csv(DATA / "jobs_1000.csv", index=False, encoding="utf-8-sig")
print("\nsaved data/jobs_1000.csv")
print(sel.head(3)[["公司", "岗位名称", "archetype", "城市", "样本层级", "相关性分", "届别"]].to_string())
