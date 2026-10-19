# 2027 秋招 AI Agent 应用 / 开发 岗位情报与开源项目匹配

> 用 **1,000 条 2027 届秋招真实在招 JD** 回答三个问题：招聘方到底在要什么能力、这些能力怎么用数据证明、以及**哪个 GitHub 项目能最高性价比地证明它**。
>
> 数据快照：2026-10-19 ｜ 覆盖 131 家公司 ｜ 75 个 GitHub 项目（API 实时校验）

![岗位族分布](report/charts/fig1_archetypes.png)

---

## 🎯 这是什么

一份面向 **2027 届秋招 AI Agent / 大模型应用方向** 的求职情报包，包含：

| 产出 | 说明 |
|---|---|
| **1,000 条标注 JD 数据集** | 含岗位职责/任职要求全文、原始链接、岗位族、关键词、相关性分 |
| **高频关键词与技能分层** | 66 个归并关键词、必备/加分/差异化三层技能、岗位族×关键词矩阵 |
| **岗位需求解析** | 12 个岗位族的规模/薪资/城市/典型岗位名/高频词；学历、城市、薪资分布 |
| **GitHub 项目匹配** | 75 个候选项目，按「含金量 × 说服力 × 可上手 × 需求匹配」打分，并给出实操任务/交付物/面试讲点 |
| **岗位族 → 项目组合** | 每个岗位族「核心作品 / 速成作品 / 硬核加分」三件套建议 |
| **90 天上手路线** | 从基础到作品集包装的阶段计划 |

## 📊 核心结论

| 指标 | 数值 |
|---|---|
| Agent/智能体 提及率 | **85.2%**（但仅 24.5% 写进岗位名） |
| 岗位族 Top3 | 算法/研究 57.0% ｜ 应用开发 24.6% ｜ AI 产品 4.9% |
| 必备技能 Top5 | 大模型/LLM 81.4% ｜ Python 74.8% ｜ RAG 46.1% ｜ 工具调用 44.5% ｜ LangChain 43.2% |
| 高性价比新信号 | **MCP 31.9%** ｜ A2A 28.3%（学习成本低、候选人少） |
| 学历门槛 | 本科 64.0% ｜ 硕士 9.1% ｜ 不限 9.9% ｜ 未明示 16.1% |
| 薪资 | 中位 **42.0 万/年**（n=146 条公开薪资，25 分位 30.2 万 / 75 分位 56.0 万） |
| 城市 | 北京 30.6% ｜ 上海 19.4% ｜ 深圳 12.3% ｜ 杭州 10.5%（四城 72.8%） |
| 项目结论 | S 级 1 个（LangChain）、A 级 3 个（Dify / 微软生成式 AI 课程 / LLaMA-Factory） |

**一句话结论**：Agent 能力已从「岗位名称」下沉为「岗位基础设施」——真正稀缺的是「能用 Agent 交付可量化结果」的证据。推荐组合：**1 个可演示核心作品（LangChain/Dify + RAG）+ 1 个协议/安全加分项（MCP）+ 1 个硬核项（微调 / 推理 / RAG 调优）**。

## 🗂 仓库结构

```
.
├── .gitignore
├── requirements.txt
├── README.md
├── report/                                    # 分析报告（md / docx / pdf + 图表）
│   ├── 2027秋招-AI_Agent岗位情报与开源项目匹配.md
│   ├── 2027秋招-AI_Agent岗位情报与开源项目匹配.docx
│   ├── 2027秋招-AI_Agent岗位情报与开源项目匹配.pdf
│   └── charts/fig1~fig6.png
├── workbook/
│   └── 2027秋招-AI_Agent岗位情报与开源项目匹配.xlsx   # 10 个 sheet 主交付物
├── data/
│   ├── jobs_1000.csv                 # 1,000 条标注 JD（核心数据集）
│   ├── jobs_all.csv                  # 4,356 条去重全量池
│   ├── jobs_social_supplement.csv    # 社招对照样本（400 条）
│   ├── keywords.csv                  # 66 个关键词的 JD 占比/岗位名占比/区分度
│   ├── skill_layers.csv              # 必备 / 加分 / 差异化技能分层
│   ├── archetypes.csv                # 12 个岗位族画像
│   ├── keyword_archetype_matrix.csv  # 关键词 × 岗位族占比矩阵
│   ├── tools_mentions.csv            # 48 个具名工具/框架的 JD 提及率
│   ├── projects.csv                  # 75 个项目的真实指标 + 四项评分
│   └── archetype_project_plan.csv    # 岗位族 × 项目组合推荐
└── scripts/                          # 全流程可复现脚本
    ├── crawl_nowcoder.py             # 牛客网岗位采集
    ├── crawl_cross2.py               # 百度 / 美团采集
    ├── normalize.py                  # 清洗、归一化、去重、相关性打分
    ├── select_1000.py                # 分层抽样出 1000 条 + 岗位族分类
    ├── analyze.py                    # 关键词统计 / 岗位族画像 / 工具提及率
    ├── fetch_repos.py                # GitHub API 拉取项目真实指标
    ├── repos_score.py                # 项目评分与岗位族→项目组合
    ├── charts.py                     # 报告图表
    ├── build_xlsx.py                 # 生成 Excel 工作簿
    ├── build_report.py               # 生成 MD / DOCX 报告
    ├── lexicon.py                    # AI Agent 领域词表（同义词归并）
    ├── repos.py                      # 75 个项目的人工 curation 数据
    └── explore/                      # 数据源探测脚本（过程留档，非必需）
```

## 🚀 快速使用

1. **先看结论**：打开 [`report/2027秋招-AI_Agent岗位情报与开源项目匹配.pdf`](report/2027秋招-AI_Agent岗位情报与开源项目匹配.pdf)（13 页）。
2. **要落地查岗**：打开 `workbook/…xlsx` 的「01-岗位样本1000」sheet，按岗位族/城市/学历筛选，用「匹配关键词」列判断算法型 vs 应用型。
3. **要选项目**：看 xlsx「07-项目匹配总表」与「08-岗位族×项目组合」，或 `data/archetype_project_plan.csv`。
4. **要复现分析**：

```bash
pip install -r requirements.txt
python scripts/analyze.py        # 依赖 data/jobs_1000.csv，可直接复现关键词与画像
python scripts/repos_score.py    # 需要先有 GitHub token + data/repos_raw.json
python scripts/charts.py         # 生成图表
python scripts/build_xlsx.py     # 生成 Excel
python scripts/build_report.py   # 生成报告
```

> 重新采集 JD 需运行 `crawl_*.py`：脚本从 `raw/*.jsonl` 读取原始数据，仓库未提交 `raw/`（体积大且可重新抓取）；`data/jobs_all.csv` 已保留全部去重后的标准化记录。

## 🧪 方法说明

- **采集**：牛客网（838 条）、百度招聘官网（157 条）、美团招聘官网（5 条）公开接口，低频访问（≥1s/请求），不登录、不绕过验证码、不破解反爬。
- **漏斗**：4,569 条原始 → 4,356 条去重 → 2,136 条技术/产品 + Agent 强信号过滤 → 1,000 条分层抽样（公司配额上限）。
- **关键词**：文档级命中（1 条 JD 多次出现只计 1 次），同义词归并（Agent / AI Agent / 智能体 → `Agent/智能体`）。
- **项目评分**：含金量 32% + 说服力 32% + 可上手 18% + 需求匹配 18%；需求匹配按「目标岗位族内」的关键词占比计算；GitHub 指标为 2026-10-19 快照。

## ⚠️ 局限

1. 样本非全量：Boss 直聘、LinkedIn 等需登录/强反爬渠道按合规要求未纳入；比例结论可参考，绝对数量不可外推。
2. 1,000 条中 258 条页面明示「2027届」，742 条为「2027届(推断)」——2026-10 时点在招的校招/实习岗即面向 2027 届，已标记区分。
3. JD 高频词反映「招聘方怎么写」，不完全等于「面试考什么」。
4. 项目「可上手程度」含人工评分（难度/上手小时），权重公开可调。

## 📄 License

[MIT](LICENSE) © 2026 Zhaojian Li
