# -*- coding: utf-8 -*-
"""第二轮机考：用 curl.exe 绕过 python TLS 指纹问题，探测各招聘源响应体。"""
import json, subprocess, time, urllib.parse

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def curl(url, post=None, form=None, ua=UA, referer=None, extra=None):
    cmd = ["curl.exe", "-s", "-L", "--compressed", "--max-time", "25",
           "-A", ua, "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8"]
    if referer:
        cmd += ["-H", "Referer: " + referer]
    for h in (extra or []):
        cmd += ["-H", h]
    if post is not None:
        cmd += ["-X", "POST", "-H", "Content-Type: application/json;charset=UTF-8",
                "--data", json.dumps(post, ensure_ascii=False)]
    if form is not None:
        cmd += ["-X", "POST", "-H", "Content-Type: application/x-www-form-urlencoded",
                "--data", urllib.parse.urlencode(form)]
    cmd.append(url)
    p = subprocess.run(cmd, capture_output=True)
    txt = p.stdout.decode("utf-8", "replace")
    return txt


def show(name, txt, n=600):
    print("=" * 20, name, "len=", len(txt))
    print(txt[:n].replace("\n", " "))
    print()


q = urllib.parse.quote("Agent")

show("meituan", curl(
    f"https://zhaopin.meituan.com/api/official/job/getJobList?pageNo=1&pageSize=5&keyword={q}"))
show("baidu", curl("https://talent.baidu.com/httservice/getPostListNew",
                   form={"recruitType": "SOCIAL", "pageSize": 5, "keyWord": "Agent",
                         "curPage": 1, "projectType": "", "postType": "",
                         "workPlace": "", "bg": ""},
                   referer="https://talent.baidu.com/jobs/social-list"))
show("bytedance", curl("https://jobs.bytedance.com/api/v1/search/job/posts",
                       post={"keyword": "Agent", "limit": 5, "offset": 0,
                             "job_category_id_list": [], "location_code_list": [],
                             "subject_id_list": [], "recruitment_id_list": [],
                             "portal_type": 6, "job_function_id_list": [],
                             "storefront_id_list": []},
                       referer="https://jobs.bytedance.com/campus/position"))
show("alibaba", curl(
    "https://talent.alibaba.com/position/search?channel=group_official_site&language=zh",
    post={"keyword": "Agent", "page": 1, "pageSize": 5},
    referer="https://talent.alibaba.com/off-campus/position-list"))
show("kuaishou", curl(
    "https://zhaopin.kuaishou.cn/recruit/e/api/v1/job/list",
    post={"keyword": "Agent", "pageNum": 1, "pageSize": 5},
    referer="https://zhaopin.kuaishou.cn/"))
show("huawei", curl(
    "https://career.huawei.com/reccampportal/services/portal/portalpub/getJobList",
    post={"curPage": 1, "pageSize": 5, "searchText": "Agent"},
    referer="https://career.huawei.com/reccampportal/portal5/social-recruitment.html"))
show("netease", curl(
    f"https://hr.163.com/api/hr163/position/queryPage?currentPage=1&pageSize=5&keyword={q}"))
show("shixiseng", curl("https://www.shixiseng.com/interns?keyword=AI%20Agent"), 400)
