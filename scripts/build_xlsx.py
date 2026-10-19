# -*- coding: utf-8 -*-
"""生成交付用 Excel 工作簿（openpyxl）：10 个 sheet + 图表嵌入。"""
import pathlib
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.drawing.image import Image as XLImage
from openpyxl.worksheet.table import Table, TableStyleInfo

D = pathlib.Path("data")
OUT = pathlib.Path("output")
CH = OUT / "charts"

jobs = pd.read_csv(D / "jobs_1000.csv")
kw = pd.read_csv(D / "keywords.csv")
layers = pd.read_csv(D / "skill_layers.csv")
arch = pd.read_csv(D / "archetypes.csv")
mat = pd.read_csv(D / "keyword_archetype_matrix.csv", index_col=0)
tools = pd.read_csv(D / "tools_mentions.csv")
proj = pd.read_csv(D / "projects.csv")
plan = pd.read_csv(D / "archetype_project_plan.csv")

NAVY = "1F3864"
BLUE = "2E5EAA"
LIGHT = "DCE6F1"
GREY = "F2F2F2"
WHITE = "FFFFFF"

hdr_font = Font(name="微软雅黑", size=10, bold=True, color=WHITE)
hdr_fill = PatternFill("solid", fgColor=NAVY)
body_font = Font(name="微软雅黑", size=9)
title_font = Font(name="微软雅黑", size=16, bold=True, color=NAVY)
sub_font = Font(name="微软雅黑", size=11, bold=True, color=BLUE)
thin = Side(style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

wb = Workbook()


def style_header(ws, row, ncol, height=26):
    ws.row_dimensions[row].height = height
    for c in range(1, ncol + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = hdr_font
        cell.fill = hdr_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border


def write_df(ws, df, start_row=1, widths=None, num_formats=None, wrap_cols=None):
    cols = list(df.columns)
    for j, c in enumerate(cols, 1):
        ws.cell(row=start_row, column=j, value=c)
    style_header(ws, start_row, len(cols))
    for i, row in enumerate(df.itertuples(index=False), start_row + 1):
        for j, v in enumerate(row, 1):
            cell = ws.cell(row=i, column=j)
            if pd.isna(v):
                v = ""
            cell.value = v
            cell.font = body_font
            cell.border = border
            cell.alignment = Alignment(vertical="top", wrap_text=(cols[j - 1] in (wrap_cols or [])))
    if widths:
        for j, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(j)].width = w
    if num_formats:
        for col, fmt in num_formats.items():
            j = cols.index(col) + 1
            for i in range(start_row + 1, start_row + 1 + len(df)):
                ws.cell(row=i, column=j).number_format = fmt
    ws.freeze_panes = ws.cell(row=start_row + 1, column=2)
    if len(df) > 0:
        ws.auto_filter.ref = f"A{start_row}:{get_column_letter(len(cols))}{start_row + len(df)}"
    return cols


# ============ Sheet 0 摘要 ============
ws = wb.active
ws.title = "00-报告摘要"
ws.sheet_view.showGridLines = False
ws["B2"] = "2027 届秋招 · AI Agent 应用/开发 岗位情报与开源项目匹配"
ws["B2"].font = title_font
ws["B3"] = "数据采集日：2026-10-19 ｜ 样本：1000 条 2027 届校招/实习在招 JD ｜ 公司：131 家 ｜ 项目：75 个（GitHub API 实时校验）"
ws["B3"].font = Font(name="微软雅黑", size=9, color="595959")

summary_rows = [
    ("核心指标", "数值", "说明"),
    ("JD 样本量", "1,000 条", "全部为 2027 届校招/实习在招岗位；来源：牛客 838 / 百度 157 / 美团 5"),
    ("覆盖公司", "131 家", "百度、华为、快手、字节、阿里、小红书、B站、美团、拼多多、SHEIN、Shopee 等"),
    ("Agent/智能体 提及率", "85.2%", "但仅 24.5% 写进岗位名称——Agent 已是通用能力词，不再是岗位标签"),
    ("岗位族 Top3", "算法/研究 57.0%｜应用开发 24.6%｜AI 产品 4.9%", "秋招 AI Agent 岗以「算法 + 工程」复合型为主"),
    ("必备技能 Top5", "大模型/LLM 81.4%｜Python 74.8%｜RAG 46.1%｜工具调用 44.5%｜LangChain 43.2%", "详见 02/03 sheet"),
    ("学历门槛", "本科 64.0%｜硕士 9.1%｜不限 9.9%｜未明示 16.1%", "81% 的 JD 提及学历要求，博士仅 0.7%"),
    ("薪资", "中位 42.0 万 / 年（n=146 条有公开薪资）", "25 分位 30.2 万，75 分位 56.0 万，最高 88 万"),
    ("城市", "北京 30.6%｜上海 19.4%｜深圳 12.3%｜杭州 10.5%", "四城合计 72.8%"),
    ("项目库", f"75 个候选 → S/A 级 {int(proj.grade.isin(['S','A']).sum())} 个、B 级 {int((proj.grade=='B').sum())} 个", "评分=含金量 32% + 说服力 32% + 可上手 18% + 需求匹配 18%（按目标岗位族计算）"),
]
r = 5
for i, row in enumerate(summary_rows):
    for j, v in enumerate(row, 2):
        cell = ws.cell(row=r, column=j, value=v)
        if i == 0:
            cell.font = hdr_font
            cell.fill = hdr_fill
        else:
            cell.font = Font(name="微软雅黑", size=9, bold=(j == 2))
            cell.fill = PatternFill("solid", fgColor=GREY if i % 2 == 0 else WHITE)
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        cell.border = border
    ws.row_dimensions[r].height = 30 if i else 24
    r += 1
ws.column_dimensions["A"].width = 2
ws.column_dimensions["B"].width = 26
ws.column_dimensions["C"].width = 62
ws.column_dimensions["D"].width = 62

ws["B17"] = "一句话结论"
ws["B17"].font = sub_font
ws["B18"] = ("Agent 能力已从「岗位名称」下沉为「岗位基础设施」：85% 的 AI 岗要求 Agent 相关能力，"
             "但只有 1/4 的岗位名带 Agent。秋招竞争点不再是「会不会 Agent」，而是"
             "「能否用 Agent 交付可量化结果」——这正是开源项目作品集能证明的东西。")
ws["B18"].font = Font(name="微软雅黑", size=10)
ws["B18"].alignment = Alignment(wrap_text=True, vertical="top")
ws.merge_cells("B18:D20")
ws.row_dimensions[18].height = 22
ws.row_dimensions[19].height = 22
ws.row_dimensions[20].height = 22

if (CH / "fig1_archetypes.png").exists():
    img = XLImage(str(CH / "fig1_archetypes.png"))
    img.width, img.height = 520, 300
    ws.add_image(img, "F5")
if (CH / "fig2_keywords.png").exists():
    img2 = XLImage(str(CH / "fig2_keywords.png"))
    img2.width, img2.height = 520, 340
    ws.add_image(img2, "F22")

# ============ Sheet 1 岗位样本 ============
ws = wb.create_sheet("01-岗位样本1000")
show = jobs[["公司", "岗位名称", "archetype", "城市", "届别", "招聘类型", "学历要求", "薪资",
             "年薪(万)", "Agent强信号数", "相关性分", "匹配关键词", "岗位职责摘要",
             "任职要求摘要", "发布时间", "原始链接"]].copy()
show.insert(0, "序号", range(1, len(show) + 1))
show = show.rename(columns={"archetype": "岗位族", "城市": "城市"})
write_df(ws, show, start_row=1,
         widths=[6, 16, 34, 16, 12, 10, 12, 10, 14, 10, 10, 10, 46, 52, 52, 10, 46],
         num_formats={"年薪(万)": "0.0"}, wrap_cols=["岗位名称", "匹配关键词", "岗位职责摘要", "任职要求摘要"])
for i in range(2, len(show) + 2):
    c = ws.cell(row=i, column=16)
    if c.value:
        c.hyperlink = str(c.value)
        c.font = Font(name="微软雅黑", size=9, color="0563C1", underline="single")

# ============ Sheet 2 关键词总榜 ============
ws = wb.create_sheet("02-关键词总榜")
k = kw[["rank", "term", "category", "doc_count", "share", "title_share",
        "in_requirements", "in_responsibilities", "top_archetype_lift"]].copy()
k.columns = ["排名", "关键词(归并后)", "类别", "命中JD数", "JD占比%", "岗位名占比%",
             "出现在任职要求%", "出现在岗位职责%", "高区分度岗位族(lift)"]
write_df(ws, k, widths=[6, 22, 16, 10, 10, 11, 14, 14, 44],
         num_formats={"JD占比%": "0.0", "岗位名占比%": "0.0",
                      "出现在任职要求%": "0.0", "出现在岗位职责%": "0.0"})
ws.conditional_formatting.add(f"E2:E{len(k)+1}",
                              ColorScaleRule(start_type="min", start_color="FFFFFF",
                                             end_type="max", end_color="2E5EAA"))

# ============ Sheet 3 技能分层 ============
ws = wb.create_sheet("03-技能分层")
l = layers[["layer", "term", "category", "share", "doc_count"]].copy()
l.columns = ["层级", "技能/关键词", "类别", "JD占比%", "命中JD数"]
write_df(ws, l, widths=[22, 24, 16, 10, 10], num_formats={"JD占比%": "0.0"})
for i in range(2, len(l) + 2):
    v = ws.cell(row=i, column=1).value
    color = {"必备(≥25% JD)": "C6EFCE", "加分(8-25%)": "FFEB9C", "差异化(2-8%)": "DDEBF7"}.get(v)
    if color:
        ws.cell(row=i, column=1).fill = PatternFill("solid", fgColor=color)

# ============ Sheet 4 岗位族画像 ============
ws = wb.create_sheet("04-岗位族画像")
a = arch[["archetype", "count", "share", "salary_median", "top_cities", "top_companies",
          "top_terms", "typical_titles"]].copy()
a.columns = ["岗位族", "JD数", "占比%", "薪资中位(万)", "主要城市", "代表公司", "该族高频关键词", "典型岗位名"]
write_df(ws, a, widths=[18, 8, 8, 12, 40, 40, 70, 60], num_formats={"占比%": "0.0", "薪资中位(万)": "0.0"},
         wrap_cols=["主要城市", "代表公司", "该族高频关键词", "典型岗位名"])

# ============ Sheet 5 矩阵 ============
ws = wb.create_sheet("05-岗位族x关键词矩阵")
m = mat.copy()
m.index.name = "关键词"
m = m.reset_index()
write_df(ws, m, widths=[24] + [14] * (len(m.columns) - 1))
if len(m.columns) > 1:
    ws.conditional_formatting.add(f"B2:{get_column_letter(len(m.columns))}{len(m)+1}",
                                  ColorScaleRule(start_type="num", start_value=0, start_color="FFFFFF",
                                                 end_type="num", end_value=100, end_color="2E5EAA"))

# ============ Sheet 6 工具提及 ============
ws = wb.create_sheet("06-工具提及率")
t = tools.copy()
t.columns = ["工具/框架/模型", "命中JD数", "JD占比%"]
write_df(ws, t, widths=[30, 12, 12], num_formats={"JD占比%": "0.0"})
ws.conditional_formatting.add(f"C2:C{len(t)+1}",
                              ColorScaleRule(start_type="min", start_color="FFFFFF",
                                             end_type="max", end_color="4C9F70"))
if (CH / "fig6_tools.png").exists():
    img = XLImage(str(CH / "fig6_tools.png"))
    img.width, img.height = 560, 350
    ws.add_image(img, "E2")

# ============ Sheet 7 项目总表 ============
ws = wb.create_sheet("07-项目匹配总表")
p = proj[["rank", "full_name", "project_type", "cluster", "stars", "forks", "pushed",
          "days_since_push", "license", "difficulty", "hours", "gpu_required",
          "score_gold", "score_persuasion", "score_hands_on", "score_match",
          "score_total", "grade", "jd_term_coverage", "tool_mention_share",
          "matched_archetypes", "task", "deliverable", "interview", "url"]].copy()
p.columns = ["排名", "项目", "类型", "能力簇", "Stars", "Forks", "最近提交", "距今(天)", "License",
             "难度(1-5)", "上手(h)", "需GPU", "含金量", "说服力", "可上手", "需求匹配",
             "综合分", "等级", "JD词覆盖", "工具提及率%", "适配岗位族", "实操任务", "交付物", "面试讲点", "链接"]
write_df(ws, p, widths=[6, 32, 22, 18, 9, 8, 11, 8, 12, 9, 9, 7, 8, 8, 8, 8, 8, 6, 9, 10, 34, 46, 34, 38, 46],
         num_formats={"综合分": "0.0", "含金量": "0.0", "说服力": "0.0", "可上手": "0.0",
                      "需求匹配": "0.0", "工具提及率%": "0.0"},
         wrap_cols=["项目", "类型", "实操任务", "交付物", "面试讲点", "适配岗位族"])
for col in ["M", "N", "O", "P", "Q"]:
    ws.conditional_formatting.add(f"{col}2:{col}{len(p)+1}",
                                  ColorScaleRule(start_type="num", start_value=40, start_color="FFFFFF",
                                                 end_type="num", end_value=100, end_color="2E5EAA"))
for i in range(2, len(p) + 2):
    c = ws.cell(row=i, column=18)
    g = c.value
    color = {"S": "FFD966", "A": "C6EFCE", "B": "DDEBF7", "C": "F2F2F2", "D": "FFEB9C"}.get(g)
    if color:
        c.fill = PatternFill("solid", fgColor=color)
        c.font = Font(name="微软雅黑", size=9, bold=True)
    link = ws.cell(row=i, column=25)
    if link.value:
        link.hyperlink = str(link.value)
        link.font = Font(name="微软雅黑", size=9, color="0563C1", underline="single")

# ============ Sheet 8 岗位族→项目组合 ============
ws = wb.create_sheet("08-岗位族x项目组合")
pl = plan.copy()
pl.columns = ["岗位族", "JD数", "占比%", "推荐项目组合（核心 / 速成 / 硬核）"]
write_df(ws, pl, widths=[18, 8, 8, 110], num_formats={"占比%": "0.0"}, wrap_cols=["推荐项目组合（核心 / 速成 / 硬核）"])

# ============ Sheet 9 来源与口径 ============
ws = wb.create_sheet("09-数据来源与口径")
ws.sheet_view.showGridLines = False
ws["B2"] = "数据来源、采集口径与局限"
ws["B2"].font = title_font
lines = [
    ("一、数据来源（均为公开可访问页面/接口，低频采集，遵守 robots 与站点条款）", True),
    ("· 牛客网岗位搜索（nowcoder.com/np-api/u/job/search）：838 条，2027 届校招/实习主战场", False),
    ("· 百度招聘官网（talent.baidu.com 公开接口）：157 条，校招/实习岗位", False),
    ("· 美团招聘官网（zhaopin.meituan.com 公开接口）：5 条，含「2026年（2027届）秋季校招」项目", False),
    ("· 未纳入：Boss 直聘、LinkedIn、脉脉等需登录/强反爬渠道（合规原因不做绕过）", False),
    ("", False),
    ("二、采集与筛选漏斗", True),
    ("原始抓取 4,569 条 → 去重（公司+岗位+城市）4,327 条 → 技术/产品类 + Agent 强信号过滤 2,136 条", False),
    ("→ 分层抽样 1,000 条（优先 2027 届校招/实习，公司配额上限控制大厂占比）", False),
    ("", False),
    ("三、字段口径", True),
    ("· 届别：258 条由页面明示「2027届」；742 条为「2027届(推断)」——2026-10 时点在招的校招/实习岗即面向 2027 届", False),
    ("· 岗位族：基于岗位名 + JD 全文的规则打分归类（12 类），可在 scripts/select_1000.py 中复现", False),
    ("· 关键词：文档级命中（1 条 JD 命中多次只计 1 次），同义词已归并（如 Agent/AI Agent/智能体）", False),
    ("· 薪资：仅 146 条 JD 公开薪资；按「月薪K × 薪数」折算年薪，实习日薪不计入", False),
    ("· 相关性分：强信号词（Agent/智能体/工具调用/MCP/RAG 等）加权，用于样本筛选，非岗位质量评价", False),
    ("", False),
    ("四、局限（请务必阅读）", True),
    ("1) 样本非全量：秋招岗位分散在数百个渠道，本表覆盖 131 家公司，不代表整个市场；", False),
    ("2) 关键词统计反映「JD 怎么写」，不等于「面试考什么」；", False),
    ("3) 项目评分中「可上手程度」含人工评分（difficulty/hours），权重可调，方法已在 07 sheet 公开；", False),
    ("4) GitHub 指标为 2026-10-19 快照，stars 会变化，引用时请以当日为准。", False),
    ("", False),
    ("五、复现方式", True),
    ("scripts/：crawl_nowcoder.py / crawl_cross2.py → normalize.py → select_1000.py → analyze.py → repos_score.py → charts.py / build_xlsx.py / build_report.py", False),
]
r = 4
for text, bold in lines:
    c = ws.cell(row=r, column=2, value=text)
    c.font = Font(name="微软雅黑", size=10, bold=bold, color=NAVY if bold else "333333")
    c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[r].height = 20 if not bold else 24
    r += 1
ws.column_dimensions["A"].width = 2
ws.column_dimensions["B"].width = 150

wb.save(OUT / "2027秋招-AI_Agent岗位情报与开源项目匹配.xlsx")
print("saved xlsx:", (OUT / "2027秋招-AI_Agent岗位情报与开源项目匹配.xlsx").resolve())
