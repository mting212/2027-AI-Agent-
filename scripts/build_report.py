# -*- coding: utf-8 -*-
"""生成 DOCX + MD 分析报告（同一份内容块，双渲染）。"""
import pathlib
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

D = pathlib.Path("data")
OUT = pathlib.Path("output")
CH = OUT / "charts"

jobs = pd.read_csv(D / "jobs_1000.csv")
kw = pd.read_csv(D / "keywords.csv")
layers = pd.read_csv(D / "skill_layers.csv")
arch = pd.read_csv(D / "archetypes.csv")
tools = pd.read_csv(D / "tools_mentions.csv")
proj = pd.read_csv(D / "projects.csv")
plan = pd.read_csv(D / "archetype_project_plan.csv")
mat = pd.read_csv(D / "keyword_archetype_matrix.csv", index_col=0)

NAVY = RGBColor(0x1F, 0x38, 0x64)
BLUE = RGBColor(0x2E, 0x5E, 0xAA)

# ---------- 内容块 ----------
B = []
B.append(("title", "2027 届秋招 AI Agent 应用/开发\n岗位情报与开源项目匹配报告"))
B.append(("meta", "数据快照：2026-10-19 ｜ 样本：1,000 条 2027 届校招/实习在招 JD ｜ 覆盖 131 家公司 ｜ 项目库：75 个（GitHub API 实时校验）"))
B.append(("h1", "一、核心结论（先看这一页）"))
B.append(("bullets", [
    "**Agent 已从「岗位标签」下沉为「岗位基础设施」**：85.2% 的 JD 提及 Agent/智能体，但只有 24.5% 把 Agent 写进岗位名。也就是说，「懂 Agent」不再是加分项，而是 AI 岗的默认门槛；真正的区分度在于「能否用 Agent 交付可量化结果」。",
    "**需求结构仍是「算法 + 工程」复合型**：Agent 算法/研究 57.0%、Agent 应用开发 24.6%、AI 产品 4.9%、AI Infra 3.9%、RAG/知识库 3.8%。纯「调 Prompt 搭 Demo」的岗位几乎不存在，JD 普遍要求同时具备大模型理解、工程实现与业务落地。",
    "**技能栈呈三层结构**：必备层（Agent/智能体 85.2%、大模型/LLM 81.4%、Python 74.8%、RAG 46.1%、工具调用 44.5%、LangChain 43.2%）；加分层（微调 49.8%、Prompt 49.0%、多智能体 34.4%、MCP 31.9%、A2A 28.3%）；差异化层（评测体系 12.7%、向量检索 10.3%、记忆管理 7.7%、GraphRAG/文档解析 3.8%、Agent 安全 0.8%、Computer Use 0.4%——出现率低、候选人更少，做出来辨识度最高）。",
    "**2026 年新增的两个高性价比信号：MCP 与 A2A**。31.9% 的 JD 直接提到 MCP、28.3% 提到 A2A，比 2025 年显著上升；这两个协议类能力学习成本低、面试辨识度高，是「低成本高回报」的差异化点。",
    "**薪资与城市**：有公开薪资的 146 条 JD 中，应届年薪中位数 **42.0 万**（25 分位 30.2 万 / 75 分位 56.0 万）；北京 30.6%、上海 19.4%、深圳 12.3%、杭州 10.5%，四城合计 72.8%。",
    "**项目匹配结论**：" + (
        f"75 个候选项目中，S 级 {int((proj.grade == 'S').sum())} 个、A 级 {int((proj.grade == 'A').sum())} 个"
        f"（{'、'.join(proj[proj.grade.isin(['S','A'])]['full_name'].str.split('/').str[-1].tolist())}）。"
        "最优策略不是「做最多项目」，而是 **「1 个可演示的核心作品 + 1 个协议/安全类加分项 + 1 个 Infra 硬核项」** 的三件套组合，详见第五章。"),
]))

B.append(("h1", "二、数据与方法"))
B.append(("h2", "2.1 数据来源"))
B.append(("p", "本次采集全部来自公开可访问的招聘页面与公开接口，采用低频访问（单站 ≥1 秒/请求），不登录、不绕过验证码、不破解反爬。具体来源与条数："))
B.append(("table", pd.DataFrame([
    ["牛客网岗位搜索", "nowcoder.com（公开搜索接口）", "838", "2027 届校招/实习主战场，含大量官方 HR 直发岗位"],
    ["百度招聘官网", "talent.baidu.com（公开接口）", "157", "校招/实习岗位，含完整职责与要求"],
    ["美团招聘官网", "zhaopin.meituan.com（公开接口）", "5", "含「2026年（2027届）秋季校招」项目的完整 JD"],
], columns=["来源渠道", "入口", "条数", "说明"]), [3.2, 5.2, 1.8, 6.8]))
B.append(("p", "**未纳入的渠道及原因**：Boss 直聘、LinkedIn、脉脉等需要登录态或存在强反爬/用户协议限制，按合规要求未做绕过；这会导致样本对「中小厂 + 社招混合岗」覆盖不足，但对「2027 届校招大厂/中厂」这一核心目标群体的覆盖是充分的。"))
B.append(("h2", "2.2 采集与筛选漏斗"))
B.append(("table", pd.DataFrame([
    ["① 原始抓取", "4,569 条", "牛客/百度/腾讯/美团 四源原始记录"],
    ["② 跨源去重", "4,356 条", "去重键 = 公司 + 岗位名 + 城市；重复时优先保留校招岗"],
    ["③ 相关性过滤", "2,136 条", "限技术/产品类岗位 + 至少 1 个 Agent 强信号（Agent/智能体/工具调用/MCP/RAG/LangChain 等）"],
    ["④ 分层抽样", "**1,000 条**", "优先 2027 届校招/实习；大厂公司配额上限（如百度 ≤160、华为 ≤90）防止单源垄断"],
], columns=["步骤", "剩余", "规则"]), [3.0, 2.6, 11.4]))
B.append(("h2", "2.3 口径与局限（务必阅读）"))
B.append(("bullets", [
    "**届别判定**：258 条由页面明示「2027届」；742 条为「2027届(推断)」——2026 年 10 月时点在招的校招/实习岗即面向 2027 届毕业生，这是合理推断而非页面直标，已在数据表中用「(推断)」标记区分。",
    "**关键词统计口径**：文档级命中（1 条 JD 命中同一词多次只计 1 次），同义词已归并（Agent / AI Agent / 智能体 → 「Agent/智能体」；RAG / 检索增强 → 「RAG/检索增强」）。因此「85.2%」的含义是「85.2% 的 JD 至少出现一次 Agent 相关表述」。",
    "**样本非全量**：1000 条是「可公开抓取 + AI Agent 相关」的子集，不代表整个秋招市场；趋势判断建议与本报告的分层结构配合使用，而非把百分比当作市场绝对值。",
    "**薪资口径**：仅 146 条 JD 公开薪资字段，按「月薪 K × 薪数」折算年薪；未公开薪资的岗位不参与统计，可能存在高薪岗位披露率偏低的偏差。",
    "**项目评分含人工判断**：「可上手程度」中的难度/上手小时数为人工评分，权重（含金量 32% / 说服力 32% / 可上手 18% / 匹配度 18%）可按需调整，评分方法完全公开，见第五章与 Excel 07 sheet。",
]))

B.append(("h1", "三、高频关键词：招聘方到底在写什么"))
B.append(("p", "下表为 1000 条 JD 中归并后的高频关键词（已剔除仅用于描述招聘对象的元词）。「JD 占比」= 含该词的 JD 数 / 1000；「岗位名占比」= 该词出现在岗位标题中的比例，二者差距能看出哪些词是「真岗位标签」、哪些只是「简历关键词」。"))
k20 = kw[~kw["category"].isin(["学历与届别"])].head(20)[["term", "category", "share", "title_share", "in_requirements"]].copy()
k20.columns = ["关键词（归并后）", "类别", "JD 占比%", "岗位名占比%", "出现在任职要求%"]
B.append(("table", k20, [4.6, 3.6, 2.2, 2.6, 2.8]))
B.append(("img", "fig2_keywords.png", "图 1  JD 高频关键词 Top20"))
B.append(("h2", "3.1 三个反直觉发现"))
B.append(("bullets", [
    "**「Agent」是语境词，不是岗位名**：85.2% 的 JD 提到 Agent，但岗位名里只有 24.5%。说明大量岗位是「大模型算法工程师」「AI 应用开发」在 JD 里要求 Agent 能力——搜索岗位时不能只搜 Agent，要搜「大模型/AI 应用/算法/应用开发」。",
    "**Python 是绝对刚需，C++/Java 是第二语言**：Python 74.8%，C++ 22.2%，Java 21.4%。Agent 应用开发岗以 Python 为主；做 Infra/端侧/高性能推理才需要 C++。",
    "**软技能不是套话**：「跨团队协作」68.9%、「学习/自驱」29.4%。Agent 岗普遍处于探索期，JD 反复强调「能快速验证、能推动落地」——这类要求往往对应「有没有真实项目从 0 到 1」的面试追问。",
]))

B.append(("h1", "四、岗位需求解析"))
B.append(("h2", "4.1 岗位族结构：算法研究主导，应用开发次之"))
B.append(("table", arch.head(8)[["archetype", "count", "share", "salary_median", "top_cities"]].rename(
    columns={"archetype": "岗位族", "count": "JD 数", "share": "占比%", "salary_median": "薪资中位(万)", "top_cities": "主要城市"}),
    [3.4, 1.8, 1.8, 2.4, 9.6]))
B.append(("img", "fig1_archetypes.png", "图 2  2027 届秋招 AI Agent 岗位族分布"))
B.append(("h2", "4.2 各族需求要点（从 JD 原文归纳）"))
B.append(("table", pd.DataFrame([
    ["Agent 算法/研究（57.0%）", "大模型训练/微调、强化学习对齐、Agent 数据合成、评测体系、论文/顶会", "高频词：微调、RLHF、GRPO、数据合成、Benchmark、顶会；典型岗名「AI Agent 大模型算法工程师」「Agentic 大模型数据合成」"],
    ["Agent 应用开发（24.6%）", "LangChain/LangGraph 编排、工具调用、RAG、后端工程、业务落地", "高频词：LangChain、Function Calling、工作流、Python/Java、接口设计；典型岗名「Agent 应用开发」「AI Agent 服务端研发」"],
    ["RAG/知识库（3.8%）", "文档解析、chunk 策略、Embedding/重排、向量库、GraphRAG", "高频词：RAG、向量数据库、Milvus/Faiss、召回、重排；常与「知识库构建与优化」绑定"],
    ["AI Infra/推理（3.9%）", "vLLM/SGLang 部署、KV cache、吞吐/延迟优化、GPU/CUDA", "高频词：推理优化、vLLM、量化、K8s、分布式；偏「平台/工程」岗"],
    ["AI 产品（4.9%）", "场景定义、需求分析、指标设计、Agent 产品化", "高频词：产品规划、用户研究、数据指标、落地；要求懂技术边界"],
    ["多模态/具身（2.7%）", "VLM、语音、视觉、机器人", "高频词：多模态、ASR/TTS、具身智能、视频理解"],
], columns=["岗位族", "核心需求", "JD 高频证据"]), [3.4, 5.8, 7.8]))
B.append(("h2", "4.3 硬门槛、软门槛与差异化能力"))
B.append(("table", pd.DataFrame([
    ["学历/届别", "本科 64.0%、硕士 9.1%、博士 0.7%、不限 9.9%、未明示 16.1%；81% JD 提及学历", "本科是主流门槛，硕士在算法/研究岗更常见；博士集中在研究型岗位"],
    ["语言/工程", "Python 74.8%、C++ 22.2%、Java 21.4%、后端/架构 20.4%、前端/全栈 13.7%", "应用开发岗几乎必考 Python + 一个后端栈；Infra 岗看 C++/CUDA"],
    ["英语/科研", "英语 31.7%、论文/顶会 20.1%、竞赛/实习 21.9%", "顶会论文是算法研究岗的强区分项；竞赛/实习是应用开发岗的证据"],
    ["城市", "北京 30.6%、上海 19.4%、深圳 12.3%、杭州 10.5%、广州 6.5%、成都 6.0%、南京 5.7%、西安 4.3%", "四城占 72.8%；成都/南京/西安是性价比选择"],
    ["薪资", "中位 42.0 万（n=146），25 分位 30.2 万，75 分位 56.0 万", "算法/研究岗中位 56.2 万，应用开发 39.0 万，产品 28.6 万"],
], columns=["维度", "数据", "解读"]), [3.0, 8.0, 6.0]))
B.append(("img", "fig3_cities.png", "图 3  岗位城市分布 Top10"))
B.append(("img", "fig4_salary.png", "图 4  应届年薪分布（n=146）"))
B.append(("h2", "4.4 具名工具/框架：项目选题的「点名率」"))
B.append(("p", "JD 里被点名的工具/框架，是最直接的「学了就能写进简历」的信号。下表为 1000 条 JD 中的具名提及率（同一 JD 多次出现只计 1 次）："))
t15 = tools.head(15).rename(columns={"tool": "工具/框架/模型", "doc_count": "命中 JD 数", "share": "JD 占比%"})
B.append(("table", t15, [5.2, 2.6, 2.6]))
B.append(("img", "fig6_tools.png", "图 5  JD 中具名工具/框架提及率"))
B.append(("bullets", [
    "**LangChain（42.7%）是唯一「不学就会被默认不会」的框架**；Framework 之争（LangChain vs LlamaIndex）在 JD 层面已经收敛，LangChain 出现率是 LlamaIndex 的 12 倍。",
    "**Function Calling（37.9%）与 MCP（31.9%）是「协议层」信号**：这两个词出现率高说明招聘方要的是「能把模型接到真实系统」的人，而不是只会聊天的人。",
    "**Dify（5.6%）、RAGFlow、FastGPT 等低代码/可视化平台的提及率不高，但实操价值极高**：它们能让你在 1-3 天内产出可演示交付物，且面试官普遍认可「用过 Dify 做过企业知识库」的工程落地感。",
]))

B.append(("h1", "五、GitHub 项目匹配：含金量 × 说服力 × 可上手"))
B.append(("h2", "5.1 评分方法"))
B.append(("p", "75 个候选项目全部通过 GitHub API 实时校验（stars / forks / 最近提交 / license / archived 状态）。综合分 = 含金量 32% + 说服力 32% + 可上手 18% + 需求匹配 18%："))
B.append(("table", pd.DataFrame([
    ["含金量（32%）", "stars 量级、最近提交活跃度、fork/star 生态比、License 合规性、是否归档"],
    ["说服力（32%）", "招聘方认可度（人工 1-5 分）+ 该项目的 JD 关键词覆盖率 + 项目具名工具在 JD 中的提及率"],
    ["可上手（18%）", "难度 1-5 分、上手小时数、是否有中文文档、是否需要 GPU"],
    ["需求匹配（18%）", "项目覆盖的 JD 高频词在「目标岗位族」JD 中的平均占比（族内占比，而非全语料均值）"],
], columns=["维度", "口径"]), [3.4, 13.6]))
B.append(("img", "fig5_projects.png", "图 6  项目含金量 × 可上手象限（气泡大小 = stars）"))
B.append(("h2", "5.2 优先项目 Top 15"))
p15 = proj.head(15)[["rank", "full_name", "project_type", "stars", "hours", "difficulty", "score_total", "grade"]].copy()
p15.columns = ["排名", "项目", "类型", "Stars", "上手(h)", "难度", "综合分", "等级"]
B.append(("table", p15, [1.4, 7.0, 4.4, 2.0, 1.8, 1.4, 1.8, 1.2]))
B.append(("h2", "5.3 S/A 级项目详解（建议至少做一个）"))
sa = proj[proj["grade"].isin(["S", "A"])]
for _, r in sa.iterrows():
    B.append(("h3", f"{r['grade']} 级 ｜ {r['full_name']}（{r['stars']:,} stars，{r['hours']} 小时上手）"))
    B.append(("bullets", [
        f"**为什么值得做**：{r['why']}。JD 关键词覆盖 {r['jd_term_coverage']}%，具名工具提及率 {r['tool_mention_share']}%。",
        f"**实操任务**：{r['task']}。",
        f"**交付物**：{r['deliverable']}。",
        f"**面试讲点**：{r['interview']}。",
    ]))
B.append(("h2", "5.4 岗位族 → 项目组合（对症下药）"))
pl = plan.copy()
pl.columns = ["岗位族", "JD 数", "占比%", "推荐项目组合（核心 / 速成 / 硬核）"]
B.append(("table", pl, [3.4, 1.6, 1.6, 10.4]))
B.append(("h2", "5.5 三件套组合建议（推荐）"))
B.append(("bullets", [
    "**核心作品（必做，2-3 周）**：LangChain 或 Dify + RAG，做一个「真实业务场景的 Agent」——例如把你的课程/实习项目文档变成知识库，做多轮问答 + 工具调用 + 引用溯源，产出可访问链接、架构图、评测数据（回答准确率、幻觉率、延迟）。这条线同时命中 JD 最高的 6 个关键词（Agent、大模型、Python、RAG、工具调用、LangChain）。",
    "**协议加成（性价比最高，3-5 天）**：MCP 官方 servers + python-sdk，写一个自定义 MCP Server（接一个真实 API），讲清协议分层、鉴权、审计。31.9% 的 JD 提 MCP，而候选人几乎都没做过——辨识度极高。",
    "**硬核项（按目标岗位族二选一，1-2 周）**：冲算法/研究 → LLaMA-Factory 微调 + DPO 对比实验；冲 Infra → vLLM 部署 + 压测调优报告；冲 RAG 工程 → RAGFlow 文档解析调优 + 召回对比。",
    "**学习型项目只做「补基础」，不做「作品集」**：hello-agents、llm-universe 等中文教程适合 1 周内补全日语体系，但简历上应体现为「产出物」，而不是「学完某教程」。",
]))

B.append(("h1", "六、30 / 60 / 90 天上手路线"))
B.append(("table", pd.DataFrame([
    ["第 1-30 天", "基础 + 第一个可跑作品", "Python 工程化补强 → LangChain/LangGraph 官方教程 → Dify 部署企业知识库 → 完成「RAG 问答 Agent」并写第一篇技术笔记"],
    ["第 31-60 天", "协议 + 工程化", "MCP python-sdk 写自定义 Server → 接入 LangChain Agent → 加可观测（LangFuse 或日志）→ 做一次「失败案例复盘」"],
    ["第 61-90 天", "差异化 + 作品集包装", "按目标岗位族选硬核项（微调/推理/RAG 调优）→ 做一份 5 页作品集（架构图 + 指标 + 复盘）→ 投递前按 JD 关键词逐条对齐简历"],
], columns=["阶段", "目标", "具体动作"]), [2.4, 4.2, 10.4]))
B.append(("p", "**投递策略**：本报告数据表（Excel 01 sheet）可直接按「岗位族 + 城市 + 学历 + 相关性分」筛选目标岗位，并用「匹配关键词」列快速判断该岗位是「算法型」还是「应用型」，从而决定投递时突出哪套项目证据。"))

B.append(("h1", "七、风险与局限"))
B.append(("bullets", [
    "**样本偏差**：1000 条来自可公开抓取的三个渠道，偏向大厂/中厂校招，缺少 Boss 直聘等渠道的中小厂岗位；比例结论可参考，绝对数量不可外推。",
    "**「2027届」含推断**：742 条为时点推断，投递前请以岗位页面实际要求为准。",
    "**JD 不等于面试**：JD 高频词反映「招聘方怎么写」，面试实际考察可能更偏项目深挖与手撕代码；建议把项目做到「能被追问 20 分钟」的深度。",
    "**项目评分的主观性**：难度/上手小时数为人工评估，不同基础的人差异较大；建议以「能否产出可演示交付物」而非「分数高低」作为最终选择标准。",
    "**工具/框架时效性**：LangChain 生态迭代快，API 可能变化；以仓库 README 与当季文档为准。",
]))

B.append(("h1", "八、附录：数据与复现"))
B.append(("bullets", [
    "**数据集**：jobs_1000.csv（1000 条标注 JD，含职责/要求全文与原始链接）、keywords.csv、skill_layers.csv、archetypes.csv、tools_mentions.csv、projects.csv、archetype_project_plan.csv；另有 jobs_all.csv（4,356 条去重全量池）与 jobs_social_supplement.csv（社招对照样本）。",
    "**Excel 工作簿**：10 个 sheet，含可筛选的 1000 条岗位表、关键词榜、技能分层、岗位族画像、矩阵、工具提及率、项目总表、项目组合与口径说明。",
    "**复现脚本**：scripts/ 下 crawl_nowcoder.py / crawl_cross2.py（采集）→ normalize.py（清洗归一）→ select_1000.py（分层抽样）→ analyze.py（关键词/画像）→ repos_score.py（项目评分）→ charts.py / build_xlsx.py / build_report.py（产出）。",
    "**数据快照日**：2026-10-19；GitHub 指标与 JD 均为该日快照，引用时请注明日期。",
]))


# ---------- MD 渲染 ----------
def render_md():
    lines = []
    for b in B:
        kind = b[0]
        if kind == "title":
            lines.append(f"# {b[1].replace(chr(10), ' ')}\n")
        elif kind == "meta":
            lines.append(f"> {b[1]}\n")
        elif kind == "h1":
            lines.append(f"\n## {b[1]}\n")
        elif kind == "h2":
            lines.append(f"\n### {b[1]}\n")
        elif kind == "h3":
            lines.append(f"\n#### {b[1]}\n")
        elif kind == "p":
            lines.append(f"{b[1]}\n")
        elif kind == "bullets":
            for x in b[1]:
                lines.append(f"- {x}")
            lines.append("")
        elif kind == "table":
            df, widths = b[1], b[2]
            lines.append("| " + " | ".join(str(c) for c in df.columns) + " |")
            lines.append("|" + "|".join(["---"] * len(df.columns)) + "|")
            for _, row in df.iterrows():
                lines.append("| " + " | ".join(str(v).replace("\n", " ") for v in row.values) + " |")
            lines.append("")
        elif kind == "img":
            lines.append(f"![{b[2]}](charts/{b[1]})\n")
    (OUT / "2027秋招-AI_Agent岗位情报与开源项目匹配.md").write_text("\n".join(lines), encoding="utf-8")
    print("md saved, chars:", len("\n".join(lines)))


# ---------- DOCX 渲染 ----------
def set_cn_font(run, name="微软雅黑", size=10.5, bold=False, color=None):
    run.font.name = name
    run.font.size = Pt(size)
    run.bold = bold
    if color is not None:
        run.font.color.rgb = color
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def render_docx():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.2)
    sec.top_margin = sec.bottom_margin = Cm(2.0)

    normal = doc.styles["Normal"]
    normal.font.name = "微软雅黑"
    normal.font.size = Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")

    for b in B:
        kind = b[0]
        if kind == "title":
            for i, txt in enumerate(b[1].split("\n")):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(txt)
                set_cn_font(r, size=18 if i == 0 else 15, bold=True, color=NAVY)
                p.paragraph_format.space_after = Pt(6)
        elif kind == "meta":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(b[1])
            set_cn_font(r, size=9, color=RGBColor(0x59, 0x59, 0x59))
            p.paragraph_format.space_after = Pt(16)
        elif kind == "h1":
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(8)
            r = p.add_run(b[1])
            set_cn_font(r, size=15, bold=True, color=NAVY)
        elif kind == "h2":
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            r = p.add_run(b[1])
            set_cn_font(r, size=12, bold=True, color=BLUE)
        elif kind == "h3":
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(b[1])
            set_cn_font(r, size=11, bold=True, color=RGBColor(0x33, 0x33, 0x33))
        elif kind == "p":
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.25
            # 解析 **bold**
            import re
            parts = re.split(r"(\*\*[^*]+\*\*)", b[1])
            for part in parts:
                if not part:
                    continue
                bold = part.startswith("**") and part.endswith("**")
                r = p.add_run(part[2:-2] if bold else part)
                set_cn_font(r, size=10.5, bold=bold)
        elif kind == "bullets":
            for x in b[1]:
                p = doc.add_paragraph(style="List Bullet")
                p.paragraph_format.space_after = Pt(3)
                p.paragraph_format.line_spacing = 1.22
                import re
                parts = re.split(r"(\*\*[^*]+\*\*)", x)
                for part in parts:
                    if not part:
                        continue
                    bold = part.startswith("**") and part.endswith("**")
                    r = p.add_run(part[2:-2] if bold else part)
                    set_cn_font(r, size=10, bold=bold)
        elif kind == "table":
            df, widths = b[1], b[2]
            tb = doc.add_table(rows=1, cols=len(df.columns))
            tb.style = "Table Grid"
            tb.alignment = WD_TABLE_ALIGNMENT.CENTER
            for j, c in enumerate(df.columns):
                cell = tb.rows[0].cells[j]
                cell.text = ""
                r = cell.paragraphs[0].add_run(str(c))
                set_cn_font(r, size=9, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                shade(cell, "1F3864")
            for _, row in df.iterrows():
                cells = tb.add_row().cells
                for j, v in enumerate(row.values):
                    cell = cells[j]
                    cell.text = ""
                    r = cell.paragraphs[0].add_run(str(v))
                    set_cn_font(r, size=8.5)
                    cell.paragraphs[0].paragraph_format.space_after = Pt(0)
            # 列宽（等比缩放到可用宽度，防止超出页面）
            usable = 16.2
            tot = sum(widths) or 1
            scale = min(1.0, usable / tot)
            tb.autofit = False
            for j, w in enumerate(widths):
                for row in tb.rows:
                    row.cells[j].width = Cm(w * scale)
            doc.add_paragraph().paragraph_format.space_after = Pt(2)
        elif kind == "img":
            path = CH / b[1]
            if path.exists():
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.add_run().add_picture(str(path), width=Cm(15.8))
                cap = doc.add_paragraph()
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = cap.add_run(b[2])
                set_cn_font(r, size=8.5, color=RGBColor(0x80, 0x80, 0x80))

    doc.save(OUT / "2027秋招-AI_Agent岗位情报与开源项目匹配.docx")
    print("docx saved")


render_md()
render_docx()
