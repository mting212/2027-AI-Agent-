# -*- coding: utf-8 -*-
import json, subprocess, re, urllib.parse, pathlib

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
RAW = pathlib.Path("raw")


def curl(url, post=None, form=None, referer=None, ua=UA, save=None):
    cmd = ["curl.exe", "-s", "-L", "--compressed", "--max-time", "25", "-A", ua,
           "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8"]
    if referer:
        cmd += ["-H", "Referer: " + referer]
    if post is not None:
        cmd += ["-X", "POST", "-H", "Content-Type: application/json;charset=UTF-8",
                "--data", json.dumps(post, ensure_ascii=False)]
    if form is not None:
        cmd += ["-X", "POST", "-H", "Content-Type: application/x-www-form-urlencoded",
                "--data", urllib.parse.urlencode(form)]
    cmd.append(url)
    p = subprocess.run(cmd, capture_output=True)
    txt = p.stdout.decode("utf-8", "replace")
    if save:
        (RAW / save).write_text(txt, encoding="utf-8")
    return txt


def head(name, txt, n=500):
    print("=" * 15, name, "len=", len(txt))
    print(txt[:n].replace("\n", " "), "\n")


q = urllib.parse.quote("Agent")

# 1) 腾讯分页与 pageSize 上限
t = curl("https://careers.tencent.com/tencentcareer/api/post/Query?timestamp=1700000000000"
         "&keyword=Agent&pageIndex=1&pageSize=100&language=zh-cn&area=cn&countryId=&cityId=&bgIds=&productId=&categoryId=&parentCategoryId=&attrId=")
try:
    j = json.loads(t)
    print("tencent pageSize=100 ->", len(j["Data"]["Posts"]), "total", j["Data"]["Count"])
except Exception as e:
    head("tencent100", t)

# 2) 腾讯校招 API
for u in ["https://careers.tencent.com/campus/tencentcareer/api/post/Query?timestamp=1700000000000&keyword=Agent&pageIndex=1&pageSize=5&language=zh-cn&area=cn",
          "https://careers.tencent.com/campus/tencentcareer/api/post/Query?timestamp=1700000000000&keyword=Agent&pageIndex=1&pageSize=5&language=zh-cn"]:
    head("tencent-campus", curl(u, referer="https://careers.tencent.com/campus/"))

# 3) 百度校招/实习 recruitType 取值
for rt in ["CAMPUS", "campus", "INTERN", "SCHOOL"]:
    t = curl("https://talent.baidu.com/httservice/getPostListNew",
             form={"recruitType": rt, "pageSize": 3, "keyWord": "Agent", "curPage": 1,
                   "projectType": "", "postType": "", "workPlace": "", "bg": ""},
             referer="https://talent.baidu.com/jobs/list")
    try:
        j = json.loads(t)
        print(f"baidu {rt}: status={j.get('status')} total={j.get('data',{}).get('total')}")
    except Exception:
        head("baidu-" + rt, t, 200)

# 4) 美团 POST
t = curl("https://zhaopin.meituan.com/api/official/job/getJobList",
         post={"pageNo": 1, "pageSize": 5, "keyword": "Agent"},
         referer="https://zhaopin.meituan.com/web/position")
head("meituan-post", t)

# 5) 实习僧搜索页 -> 提取岗位链接
t = curl("https://www.shixiseng.com/interns?keyword=AI%20Agent", save="shixiseng_search.html")
links = re.findall(r'/intern/([0-9a-f]{24})', t)
print("shixiseng intern links:", len(set(links)), list(dict.fromkeys(links))[:5])
print("has __NUXT__:", "__NUXT__" in t, "| has job titles:", t.count("intern-detail"))
if links:
    d = curl("https://www.shixiseng.com/intern/" + links[0], save="shixiseng_detail.html")
    head("shixiseng-detail", d, 300)
    print("detail has 职位描述:", "职位描述" in d or "岗位职责" in d or "__NUXT__" in d)

# 6) 应届生搜索
t = curl("https://www.yingjiesheng.com/", save="yjs_home.html")
head("yingjiesheng-home", t, 300)

# 7) 猎聘
t = curl("https://www.liepin.com/zhaopin/?key=Agent", save="liepin.html")
print("liepin len", len(t), "| __NEXT_DATA__:", "__NEXT_DATA__" in t, "| job count markers:", t.count("job-card"))

# 8) 牛客
for u in ["https://gw-c.nowcoder.com/api/sparta/job/search/job-list?query=Agent&page=1&pageSize=5&recruitType=1",
          "https://gw-c.nowcoder.com/api/sparta/job/search/list?query=Agent&page=1&pageSize=5&recruitType=1"]:
    head("nowcoder", curl(u, referer="https://www.nowcoder.com/jobs/fulltime/center"), 300)
