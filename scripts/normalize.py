# -*- coding: utf-8 -*-
"""归一化：nowcoder / tencent / baidu / meituan 原始记录 -> 统一 JD 表
输出 data/jobs_all.csv（全量池，含相关性评分与来源分层）
"""
import json, re, pathlib, hashlib, datetime
import pandas as pd

RAW = pathlib.Path("raw")
OUT = pathlib.Path("data")
OUT.mkdir(exist_ok=True)
NOW = datetime.datetime(2026, 10, 19)

# ---------------- 工具 ----------------

def ts2date(ms):
    if not ms:
        return ""
    try:
        return datetime.datetime.fromtimestamp(int(ms) / 1000).strftime("%Y-%m-%d")
    except Exception:
        return ""


def clean(t):
    if not t:
        return ""
    t = str(t).replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t\u3000]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


RESP_H = re.compile(r"(岗位职责|工作职责|职位职责|职责描述|工作内容|你将负责|你将会做|主要职责|职责：|What you.{0,3}ll do|What the Role Entails|Responsibilities|Role and Responsibilities|你将参与)", re.I)
REQ_H = re.compile(r"(任职要求|岗位要求|职位要求|任职资格|能力要求|任职条件|我们希望|我们希望你|你需要具备|要求：|加分项|优先条件|Who We Look For|Requirements|Qualifications|What we.{0,3}re looking for|Nice to have|Preferred)", re.I)


def split_jd(text):
    """把一整段 JD 拆成 职责 / 要求 / 加分项。"""
    text = clean(text)
    if not text:
        return "", "", ""
    idx_req = None
    m = REQ_H.search(text)
    if m:
        idx_req = m.start()
    idx_resp = None
    m2 = RESP_H.search(text)
    if m2:
        idx_resp = m2.start()
    bonus = ""
    mb = re.search(r"(加分项|优先条件|Nice to have|Preferred Qualifications|Bonus)", text, re.I)
    if mb:
        bonus = clean(text[mb.start():mb.start() + 600])
    if idx_resp is not None and idx_req is not None and idx_req > idx_resp:
        resp = clean(text[idx_resp:idx_req])
        req = clean(text[idx_req:])
    elif idx_req is not None:
        resp = clean(text[:idx_req]) if idx_req > 0 else ""
        req = clean(text[idx_req:])
    elif idx_resp is not None:
        resp, req = clean(text[idx_resp:]), ""
    else:
        resp, req = text, ""
    return resp, req, bonus


# 企业名归一
ALIAS = [
    (r"^上海华为.*|^华为.*|^HUAWEI.*", "华为"), (r"^阿里.*|^阿里巴巴.*|^Alibaba.*", "阿里巴巴"),
    (r"^字节.*|^ByteDance.*|^北京字节.*", "字节跳动"), (r"^腾讯.*|^Tencent.*", "腾讯"),
    (r"^百度.*|^Baidu.*", "百度"), (r"^美团.*|^Meituan.*", "美团"),
    (r"^拼多多.*|^PDD.*", "拼多多"), (r"^快手.*|^Kuaishou.*", "快手"),
    (r"^小红书.*|^Xiaohongshu.*|^行吟.*", "小红书"), (r"^蚂蚁.*|^Ant.*", "蚂蚁集团"),
    (r"^京东.*|^JD.*", "京东"), (r"^小米.*|^Xiaomi.*", "小米"), (r"^OPPO.*", "OPPO"),
    (r"^vivo.*|^维沃.*", "vivo"), (r"^荣耀.*|^HONOR.*", "荣耀"), (r"^网易.*|^NetEase.*", "网易"),
    (r"^理想.*|^Li\s*Auto.*", "理想汽车"), (r"^蔚来.*|^NIO.*", "蔚来"),
    (r"^小鹏.*|^XPENG.*", "小鹏汽车"), (r"^比亚迪.*|^BYD.*", "比亚迪"),
    (r"^科大讯飞.*|^iFLYTEK.*", "科大讯飞"), (r"^商汤.*|^SenseTime.*", "商汤科技"),
    (r"^智谱.*|^Zhipu.*", "智谱AI"), (r"^MiniMax.*", "MiniMax"),
    (r"^月之暗面.*|^Moonshot.*", "月之暗面"), (r"^阶跃.*|^StepFun.*", "阶跃星辰"),
    (r"^DeepSeek.*|^深度求索.*", "DeepSeek"), (r"^无问芯穹.*", "无问芯穹"),
    (r"^硅基流动.*|^SiliconFlow.*", "硅基流动"), (r"^携程.*|^Trip.*", "携程"),
    (r"^滴滴.*|^DiDi.*", "滴滴"), (r"^得物.*|^Dewu.*", "得物"), (r"^哔哩哔哩.*|^B站.*|^Bilibili.*", "哔哩哔哩"),
    (r"^大疆.*|^DJI.*", "大疆"), (r"^奇安信.*", "奇安信"), (r"^深信服.*", "深信服"),
    (r"^中兴.*|^ZTE.*", "中兴通讯"), (r"^中国电信.*", "中国电信"), (r"^中国移动.*", "中国移动"),
    (r"^中电科.*|^中国电子科技.*", "中国电科"), (r"^国家电网.*", "国家电网"),
]


def norm_company(name):
    if not name:
        return "未知"
    n = clean(name)
    for pat, canon in ALIAS:
        if re.search(pat, n, re.I):
            return canon
    n = re.sub(r"（.*?）|\(.*?\)", "", n)
    n = re.sub(r"(股份有限公司|有限责任公司|有限公司|集团|公司)$", "", n).strip()
    return n or "未知"


ROLE_TECH = re.compile(r"开发|研发|工程师|算法|架构|技术|后端|前端|全栈|服务端|客户端|测试|运维|数据|Infra|SRE|科学家|研究员|实习|intern|engineer|developer|scientist", re.I)
ROLE_PROD = re.compile(r"产品|PM|Product", re.I)
ROLE_BAD = re.compile(r"销售|商务|BD|市场|地推|客服|行政|人力|HR|财务|法务|采购|供应链|物流|经纪人|店长|主播|运营专员", re.I)


def role_domain(title):
    if ROLE_TECH.search(title):
        return "技术研发"
    if ROLE_PROD.search(title):
        return "产品"
    if ROLE_BAD.search(title):
        return "非技术/业务"
    return "其他"


EDU = {5000: "本科", 6000: "硕士", 7000: "博士", 0: "不限", 3000: "大专", 4000: "大专"}

GRAD_PAT = re.compile(r"(20\d{2})\s*届|(20\d{2})\s*年?校园招聘|20(\d{2})\s*届")


def grad_from_text(*texts):
    for t in texts:
        if not t:
            continue
        m = GRAD_PAT.search(str(t))
        if m:
            y = m.group(1) or m.group(2)
            if y:
                return y + "届"
    return ""


rows = []

# ---------------- 牛客 ----------------
p = RAW / "nowcoder_raw.jsonl"
if p.exists():
    with p.open(encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            try:
                ext = json.loads(r.get("ext") or "{}")
            except Exception:
                ext = {}
            jd = clean(ext.get("requirements") or "")
            strength = clean(ext.get("jobStrength") or "")
            if strength:
                jd = jd + "\n\n【岗位亮点】" + strength
            title = clean(r.get("jobName"))
            comp = ""
            for idn in (r.get("user") or {}).get("identity") or []:
                if idn.get("companyName"):
                    comp = idn["companyName"]
                    break
            if not comp:
                comp = clean(r.get("companyName") or "")
            rt = r.get("recruitType")
            rt_map = {1: "校招全职", 2: "实习", 3: "社招"}
            resp, req, bonus = split_jd(jd)
            gy = clean(r.get("graduationYear") or "")
            if gy in ("毕业不限", ""):
                gy = grad_from_text(title, jd) or "不限"
            s_min, s_max, s_mon = r.get("salaryMin"), r.get("salaryMax"), r.get("salaryMonth")
            try:
                s_min = float(s_min) if s_min not in (None, "") else None
                s_max = float(s_max) if s_max not in (None, "") else None
            except Exception:
                s_min = s_max = None
            salary, salary_wan = "", None
            if s_min:
                if s_min >= 100:  # 日薪口径（实习）
                    salary = f"{int(s_min)}-{int(s_max or s_min)}/天"
                elif s_mon and int(s_mon) > 0:
                    salary = f"{int(s_min)}-{int(s_max or s_min)}K×{int(s_mon)}薪"
                    ann = (s_min + (s_max or s_min)) / 2 * float(s_mon) / 10
                    salary_wan = round(ann, 1) if ann <= 200 else None
            rows.append(dict(
                job_id=f"nc{r.get('id')}", source="牛客网", source_name="牛客网(nc)",
                company_raw=comp, company=norm_company(comp), title=title,
                job_family_raw=clean(r.get("jobKeys") or ""), city=clean(r.get("jobCity")),
                grad_year=gy, recruit_type=rt_map.get(rt, "未知"),
                edu_req=EDU.get(r.get("eduLevel"), ""), salary_text=salary, salary_wan=salary_wan,
                jd_text=jd, responsibilities=resp, requirements=req, bonus=bonus,
                industry=clean(r.get("industryName") or ""),
                work_years_req=clean(str(r.get("workYearType") or "")),
                publish_date=ts2date(r.get("createTime")), deadline=ts2date(r.get("deliverEnd")),
                url=f"https://www.nowcoder.com/jobs/detail/{r.get('id')}",
                source_query=r.get("_query", ""), project_name="", collected_at="2026-10-19",
            ))

# ---------------- 腾讯 ----------------
p = RAW / "tencent_raw.jsonl"
if p.exists():
    with p.open(encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            jd = clean(r.get("Responsibility"))
            resp, req, bonus = split_jd(jd)
            title = clean(r.get("RecruitPostName"))
            rows.append(dict(
                job_id=f"tx{r.get('PostId')}", source="腾讯招聘官网", source_name="腾讯(tx)",
                company_raw="腾讯", company="腾讯", title=title,
                job_family_raw=clean(r.get("CategoryName") or ""),
                city=clean(r.get("LocationName")), grad_year=grad_from_text(title, jd) or "不限",
                recruit_type="官方站(社招/校招混合)", edu_req="",
                salary_text="", salary_wan=None, jd_text=jd, responsibilities=resp,
                requirements=req, bonus=bonus, industry=clean(r.get("BGName") or ""),
                work_years_req=clean(r.get("RequireWorkYearsName") or ""),
                publish_date=clean(r.get("LastUpdateTime") or ""), deadline="",
                url=clean(r.get("PostURL") or ""), source_query=r.get("_query", ""),
                project_name="", collected_at="2026-10-19",
            ))

# ---------------- 百度 ----------------
p = RAW / "baidu_raw.jsonl"
if p.exists():
    with p.open(encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            resp = clean(r.get("workContent"))
            req = clean(r.get("serviceCondition"))
            title = clean(r.get("name"))
            rt = r.get("_recruit_type", "")
            rt_map = {"校招": "校招全职", "INTERN": "实习", "SOCIAL": "社招"}
            rows.append(dict(
                job_id=f"bd{r.get('postId')}", source="百度招聘官网", source_name="百度(bd)",
                company_raw="百度", company="百度", title=title,
                job_family_raw=clean(r.get("postType") or ""), city=clean(r.get("workPlace")),
                grad_year=grad_from_text(title, resp, req) or "不限",
                recruit_type=rt_map.get(rt, rt), edu_req=clean(r.get("education") or ""),
                salary_text="", salary_wan=None, jd_text=resp + "\n" + req,
                responsibilities=resp, requirements=req, bonus="",
                industry=clean(r.get("bgShortName") or ""),
                work_years_req=clean(r.get("workYears") or ""),
                publish_date=clean(r.get("publishDate") or ""), deadline="",
                url=f"https://talent.baidu.com/jobs/detail/{r.get('postId')}",
                source_query=r.get("_query", ""), project_name="", collected_at="2026-10-19",
            ))

# ---------------- 美团 ----------------
p = RAW / "meituan_raw.jsonl"
if p.exists():
    with p.open(encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            resp = clean(r.get("jobDuty"))
            req = clean(r.get("jobRequirement"))
            title = clean(r.get("name"))
            city = ",".join([c.get("name", "") for c in (r.get("cityList") or []) if c.get("name")])
            proj = clean(r.get("projectName") or "")
            jt = str(r.get("jobType") or "")
            jt_map = {"1": "校招全职", "2": "实习", "3": "社招"}
            rows.append(dict(
                job_id=f"mt{r.get('jobUnionId')}", source="美团招聘官网", source_name="美团(mt)",
                company_raw="美团", company="美团", title=title,
                job_family_raw=clean(r.get("jobFamily") or ""), city=city,
                grad_year=grad_from_text(proj, title, resp, req) or "不限",
                recruit_type=jt_map.get(jt, jt), edu_req="", salary_text="", salary_wan=None,
                jd_text=resp + "\n" + req, responsibilities=resp, requirements=req, bonus="",
                industry=clean(r.get("jobFamilyGroup") or ""),
                work_years_req=clean(r.get("workYear") or ""),
                publish_date=ts2date(r.get("firstPostTime")), deadline=ts2date(r.get("expiredTime")),
                url=f"https://zhaopin.meituan.com/web/position/detail?jobUnionId={r.get('jobUnionId')}",
                source_query=r.get("_query", ""), project_name=proj, collected_at="2026-10-19",
            ))

df = pd.DataFrame(rows)
print("raw rows:", len(df))
print(df["source"].value_counts().to_string())

# ---------------- 城市归一 ----------------
CITY_NAMES = ["北京", "上海", "深圳", "广州", "杭州", "成都", "南京", "武汉", "西安", "苏州",
              "厦门", "长沙", "合肥", "天津", "重庆", "青岛", "济南", "郑州", "东莞", "佛山",
              "珠海", "宁波", "无锡", "福州", "大连", "沈阳", "哈尔滨", "长春", "石家庄",
              "太原", "南昌", "贵阳", "昆明", "南宁", "海口", "兰州", "香港", "新加坡",
              "东京", "首尔", "纽约", "西雅图", "伦敦"]


def norm_city(c):
    if not c:
        return ""
    parts = []
    for tok in re.split(r"[,，/、;；]", str(c)):
        tok = tok.strip()
        if not tok:
            continue
        found = ""
        for cn in CITY_NAMES:
            if tok.startswith(cn):
                found = cn
                break
        if not found:
            found = re.sub(r"(市|省|特别行政区)$", "", tok)[:8]
        parts.append(found)
    return ",".join(dict.fromkeys(parts))


df["city"] = df["city"].map(norm_city)

# ---------------- 相关性打分 ----------------
import lexicon
PATS = [(c, cat, re.compile("|".join(pat), re.I)) for c, cat, pat in lexicon.TERMS]

STRONG = {"Agent/智能体", "多智能体", "Agent开发", "工具调用/Function Calling", "工作流/编排",
          "MCP协议", "Computer Use/GUI", "任务规划/自主决策", "记忆管理/上下文", "A2A/多代理协作",
          "RAG/检索增强", "知识库", "LangChain/生态框架", "低代码Agent平台",
          "代码智能体", "自主演化/长程任务", "Agent安全/护栏", "GraphRAG/文档解析"}
MID = {"大模型/LLM", "微调/Fine-tune", "强化学习/对齐", "推理优化", "评测/Benchmark",
       "多模态", "Prompt工程", "向量数据库/检索", "Embedding/召回", "云原生/部署",
       "分布式训练", "具身智能/机器人", "智能客服/对话", "数据分析/BI"}
TITLE_STRONG = re.compile(r"Agent|智能体", re.I)
TITLE_MID = re.compile(r"大模型|LLM|AI应用|AI开发|AIGC|RAG|AI产品|Agentic", re.I)


def relevance(title, text):
    s = 0
    hits = []
    strong_hits = 0
    for canon, cat, pat in PATS:
        in_title = bool(pat.search(title or ""))
        in_text = bool(pat.search(text or ""))
        if not (in_title or in_text):
            continue
        hits.append(canon)
        if canon in STRONG:
            strong_hits += 1
            s += 6 if in_title else 3
        elif canon in MID:
            s += 2
        else:
            s += 1
    if TITLE_STRONG.search(title or ""):
        s += 8
    elif TITLE_MID.search(title or ""):
        s += 4
    return s, hits, strong_hits


rel = [relevance(t, j) for t, j in zip(df["title"], df["jd_text"])]
df["rel_score"] = [x[0] for x in rel]
df["strong_hits"] = [x[2] for x in rel]
df["rel_terms"] = ["|".join(x[1][:14]) for x in rel]
df["title_hit"] = df["title"].map(lambda t: bool(TITLE_STRONG.search(t or "") or TITLE_MID.search(t or "")))
df["role_domain"] = df["title"].map(role_domain)
df["jd_len"] = df["jd_text"].str.len()

# 去重：公司+标题+城市
def norm_title(t):
    return re.sub(r"[\s\-_/（）()【】\[\]·、，,。]+", "", str(t or "")).lower()


df["_dedup"] = (df["company"] + "|" + df["title"].map(norm_title) + "|" + df["city"].fillna(""))
df["_prio"] = df["recruit_type"].map({"校招全职": 0, "实习": 1, "社招": 2}).fillna(3)
df = df.sort_values(["_dedup", "_prio", "jd_len"], ascending=[True, True, False])
before = len(df)
dup = df.duplicated("_dedup", keep="first")
df = df[~dup].copy()
print(f"dedup: {before} -> {len(df)}")

df = df.drop(columns=["_dedup", "_prio"])

# 届别推断：2026 年 10 月正值 2027 届秋招，校招/实习岗默认面向 2027 届
def eff_grad(r):
    gy = str(r["grad_year"])
    if gy and gy != "不限":
        return gy
    if r["recruit_type"] in ("校招全职", "实习"):
        return "2027届(推断)"
    if r["source"] == "美团招聘官网" and "2027" in str(r.get("project_name") or ""):
        return "2027届(推断)"
    if "2027" in str(r["title"]):
        return "2027届(推断)"
    return "不限"


df["grad_year_eff"] = df.apply(eff_grad, axis=1)

# 分层：优先秋招/校招 > 实习 > 社招
def tier(r):
    if "2027届" in r["grad_year_eff"] and r["recruit_type"] in ("校招全职", "实习", "官方站(社招/校招混合)"):
        return "A-秋招/校招"
    if r["recruit_type"] == "校招全职":
        return "A-秋招/校招"
    if r["recruit_type"] == "实习":
        return "B-实习(转正/秋招实习)"
    return "C-社招(画像补充)"


df["sample_tier"] = df.apply(tier, axis=1)
df = df.sort_values(["rel_score", "jd_len"], ascending=False)
df.to_csv(OUT / "jobs_all.csv", index=False, encoding="utf-8-sig")
print("saved", OUT / "jobs_all.csv", len(df))
print("\nrel_score 分布:")
print(df["rel_score"].describe().to_string())
print("\nrel>=8:", (df.rel_score >= 8).sum(), "| >=5:", (df.rel_score >= 5).sum(),
      "| >=3:", (df.rel_score >= 3).sum())
print("\ncompany top20:\n", df["company"].value_counts().head(20).to_string())
print("\nrecruit_type:\n", df["recruit_type"].value_counts().to_string())
print("\ngrad_year:\n", df["grad_year"].value_counts().head(10).to_string())
