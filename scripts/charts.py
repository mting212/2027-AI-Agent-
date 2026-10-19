# -*- coding: utf-8 -*-
"""生成图表 PNG（中文），供报告与 Excel 嵌入。"""
import pathlib
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

OUT = pathlib.Path("output")
CH = OUT / "charts"
CH.mkdir(parents=True, exist_ok=True)

# 中文字体
for name in ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC"]:
    try:
        font_manager.findfont(name, fallback_to_default=False)
        plt.rcParams["font.sans-serif"] = [name]
        break
    except Exception:
        continue
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 150

D = pathlib.Path("data")
kw = pd.read_csv(D / "keywords.csv")
arch = pd.read_csv(D / "archetypes.csv")
tools = pd.read_csv(D / "tools_mentions.csv")
jobs = pd.read_csv(D / "jobs_1000.csv")
proj = pd.read_csv(D / "projects.csv")

C = ["#2E5EAA", "#4C9F70", "#E8A33D", "#C0504D", "#7D6BA6", "#5B9BD5", "#8FA8C8"]

# 1. 岗位族分布
fig, ax = plt.subplots(figsize=(8, 4.6))
a = arch.sort_values("count")
ax.barh(a["archetype"], a["count"], color=C[0])
for y, (v, s) in enumerate(zip(a["count"], a["share"])):
    ax.text(v + 6, y, f"{v} ({s}%)", va="center", fontsize=8)
ax.set_xlabel("JD 数量（共 1000 条）")
ax.set_title("2027 届秋招 AI Agent 岗位族分布", fontsize=12, fontweight="bold")
ax.set_xlim(0, a["count"].max() * 1.25)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(CH / "fig1_archetypes.png", bbox_inches="tight")
plt.close()

# 2. 高频关键词 Top20（排除纯学历/素养词）
k = kw[~kw["category"].isin(["学历与届别"])].head(20).sort_values("doc_count")
colors = [C[0] if c in ("智能体与编排", "协议与生态") else C[1] if c in ("检索增强与知识库",)
          else C[2] if c in ("大模型基础", "大模型训练", "推理与Infra") else C[4] for c in k["category"]]
fig, ax = plt.subplots(figsize=(8.6, 5.6))
ax.barh(k["term"], k["share"], color=colors)
for y, v in enumerate(k["share"]):
    ax.text(v + 0.8, y, f"{v}%", va="center", fontsize=8)
ax.set_xlabel("出现该词的 JD 占比（%）")
ax.set_title("JD 高频关键词 Top20（n=1000）", fontsize=12, fontweight="bold")
ax.set_xlim(0, k["share"].max() * 1.18)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(CH / "fig2_keywords.png", bbox_inches="tight")
plt.close()

# 3. 城市分布
city = jobs["城市"].fillna("").str.split(",").explode().str.strip()
city = city[city != ""].value_counts().head(10)
fig, ax = plt.subplots(figsize=(7.6, 4.2))
ax.bar(city.index, city.values, color=C[5])
for x, v in enumerate(city.values):
    ax.text(x, v + 2, str(v), ha="center", fontsize=8)
ax.set_ylabel("JD 数量")
ax.set_title("岗位城市分布 Top10", fontsize=12, fontweight="bold")
ax.spines[["top", "right"]].set_visible(False)
plt.xticks(rotation=25)
plt.tight_layout()
plt.savefig(CH / "fig3_cities.png", bbox_inches="tight")
plt.close()

# 4. 薪资分布
sal = jobs["年薪(万)"].dropna()
fig, ax = plt.subplots(figsize=(7.6, 4.2))
ax.hist(sal, bins=14, color=C[1], edgecolor="white")
ax.axvline(sal.median(), color=C[3], linestyle="--", label=f"中位数 {sal.median():.0f} 万")
ax.set_xlabel("应届年薪（万元，n=%d 条有薪资）" % len(sal))
ax.set_ylabel("JD 数量")
ax.set_title("2027 届 AI Agent 岗位薪资分布", fontsize=12, fontweight="bold")
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(CH / "fig4_salary.png", bbox_inches="tight")
plt.close()

# 5. 项目象限（含金量 vs 可上手，气泡=stars）
fig, ax = plt.subplots(figsize=(9, 5.8))
sub = proj[proj["score_total"] >= 55]
cmap = {"作品型(可演示/可写简历)": C[0], "基础设施型(硬核加分)": C[2], "学习型(打基础)": C[1]}
for t, g in sub.groupby("project_type"):
    ax.scatter(g["score_hands_on"], g["score_gold"], s=np.clip(np.log10(g["stars"] + 10) * 22, 18, 150),
               alpha=0.75, label=t, color=cmap.get(t, C[4]), edgecolor="white", linewidth=0.6)
for _, r in proj.head(14).iterrows():
    ax.annotate(r["full_name"].split("/")[-1], (r["score_hands_on"], r["score_gold"]),
                fontsize=7, xytext=(4, 3), textcoords="offset points")
ax.set_xlabel("可上手程度（越高越容易 1-3 天跑通并写进简历）")
ax.set_ylabel("项目含金量（stars/活跃度/生态/许可）")
ax.set_title("GitHub 项目：含金量 × 可上手象限（气泡大小=stars）", fontsize=12, fontweight="bold")
ax.axvline(75, color="grey", lw=0.8, ls=":")
ax.axhline(75, color="grey", lw=0.8, ls=":")
ax.text(76, 96, "优先：高含金量 + 易上手", fontsize=8, color="grey")
ax.legend(frameon=False, fontsize=8, loc="lower left")
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(CH / "fig5_projects.png", bbox_inches="tight")
plt.close()

# 6. 具名工具提及率
t = tools[tools["doc_count"] >= 20].sort_values("doc_count").tail(15)
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(t["tool"], t["share"], color=C[4])
for y, v in enumerate(t["share"]):
    ax.text(v + 0.4, y, f"{v}%", va="center", fontsize=8)
ax.set_xlabel("JD 提及率（%）")
ax.set_title("JD 中具名工具/框架提及率（可直接对标项目）", fontsize=12, fontweight="bold")
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(CH / "fig6_tools.png", bbox_inches="tight")
plt.close()

print("charts:", [p.name for p in CH.glob("*.png")])
