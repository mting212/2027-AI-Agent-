# -*- coding: utf-8 -*-
"""探测可公开抓取的 JD 数据源。只读、低频、单次。"""
import json, time, sys
import requests

requests.packages.urllib3.disable_warnings()

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
H = {"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"}

TESTS = []

def add(name, method, url, **kw):
    TESTS.append((name, method, url, kw))

# ---------- 企业校招 / 社招公开 API ----------
add("tencent", "GET",
    "https://careers.tencent.com/tencentcareer/api/post/Query?timestamp=1700000000000"
    "&countryId=&cityId=&bgIds=&productId=&categoryId=&parentCategoryId=&attrId="
    "&keyword=Agent&pageIndex=1&pageSize=10&language=zh-cn&area=cn")
add("bytedance", "POST",
    "https://jobs.bytedance.com/api/v1/search/job/posts",
    json={"keyword": "Agent", "limit": 10, "offset": 0, "job_category_id_list": [],
          "location_code_list": [], "subject_id_list": [], "recruitment_id_list": [],
          "portal_type": 6, "job_function_id_list": [], "storefront_id_list": []},
    headers={**H, "Content-Type": "application/json"})
add("meituan", "GET",
    "https://zhaopin.meituan.com/api/official/job/getJobList?pageNo=1&pageSize=10&keyword=Agent")
add("baidu", "POST", "https://talent.baidu.com/httservice/getPostListNew",
    data={"recruitType": "SOCIAL", "pageSize": 10, "keyWord": "Agent", "curPage": 1,
          "projectType": "", "postType": "", "workPlace": "", "bg": ""})
add("alibaba", "GET",
    "https://talent.alibaba.com/position/search?channel=group_official_site&language=zh"
    "&batchId=&keyword=Agent&page=1")
add("huawei", "GET",
    "https://career.huawei.com/reccampportal/services/portal/portalpub/getJobList"
    "?curPage=1&pageSize=10&searchText=Agent&jobFamClsCode=")
add("xiaomi", "GET", "https://hr.xiaomi.com/api/v1/positions?page=1&pageSize=10&keyword=Agent")
add("jd", "GET",
    "https://zhaopin.jd.com/web/job/job_info_list?pageIndex=1&pageSize=10&keyword=Agent")
add("kuaishou", "GET",
    "https://zhaopin.kuaishou.cn/recruit/e/api/v1/job/list?keyword=Agent&pageNum=1&pageSize=10")
add("xiaohongshu", "GET",
    "https://job.xiaohongshu.com/api/position/list?keyword=Agent&pageNum=1&pageSize=10")
add("ant", "GET",
    "https://talent.antgroup.com/api/position/search?keyword=Agent&page=1&pageSize=10")

# ---------- 综合招聘 / 校招站 ----------
add("zhaopin", "GET",
    "https://fe-api.zhaopin.com/c/i/search/positions?start=0&pageSize=10&keyword=Agent")
add("51job", "GET",
    "https://we.51job.com/api/job/search-pc?api_key=51job&timestamp=1700000000000"
    "&keyword=Agent&searchType=2&pageNum=1&pageSize=10&source=1&sortType=0")
add("yingjiesheng", "GET", "https://www.yingjiesheng.com/")
add("shixiseng", "GET", "https://www.shixiseng.com/interns?keyword=AI%20Agent")
add("nowcoder", "GET", "https://www.nowcoder.com/jobs/recommend?recruitType=1")
add("liepin", "GET", "https://www.liepin.com/zhaopin/?key=Agent")

# ---------- 其它信号源 ----------
add("github_api", "GET",
    "https://api.github.com/search/repositories?q=ai+agent&sort=stars&per_page=5")

out = []
for name, method, url, kw in TESTS:
    t0 = time.time()
    rec = {"name": name}
    try:
        if method == "GET":
            r = requests.get(url, headers={**H, **kw.get("headers", {})},
                             timeout=20, verify=False)
        else:
            r = requests.post(url, headers={**H, **kw.get("headers", {})},
                              json=kw.get("json"), data=kw.get("data"), timeout=20, verify=False)
        rec.update(status=r.status_code, bytes=len(r.content),
                   ctype=r.headers.get("content-type", "")[:60],
                   ms=int((time.time() - t0) * 1000),
                   head=r.text[:220].replace("\n", " "))
    except Exception as e:
        rec.update(status="ERR", err=repr(e)[:200])
    out.append(rec)
    print(json.dumps(rec, ensure_ascii=False), flush=True)
    time.sleep(1.2)

with open("raw/recon.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
