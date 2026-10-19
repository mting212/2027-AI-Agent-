# -*- coding: utf-8 -*-
import json, subprocess, urllib.parse, pathlib, re, time

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
RAW = pathlib.Path("raw")
JAR = str(RAW / "cookies.txt")


def curl(url, post=None, form=None, referer=None, save=None, retries=2):
    for attempt in range(retries + 1):
        cmd = ["curl.exe", "-s", "-L", "--compressed", "--max-time", "30", "-A", UA,
               "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8",
               "-c", JAR, "-b", JAR]
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
        if txt.strip():
            break
        time.sleep(3)
    if save:
        (RAW / save).write_text(txt, encoding="utf-8")
    return txt


def brief(name, t, n=300):
    print("=" * 12, name, "len=", len(t), "|", t[:n].replace("\n", " "))


# 先访问首页拿 cookie
curl("https://zhaopin.meituan.com/web/position", save="mt_home.html")
time.sleep(1)

t = curl("https://zhaopin.meituan.com/api/official/job/getJobList",
         post={"pageNo": 1, "pageSize": 2, "keyword": "Agent"},
         referer="https://zhaopin.meituan.com/web/position")
print("meituan len", len(t), t[:200])
try:
    j = json.loads(t)
    item = j["data"]["list"][0]
    print("meituan item keys:", list(item.keys()))
    print(json.dumps(item, ensure_ascii=False)[:1000])
    jid = item.get("jobUnionId")
    time.sleep(1)
    d = curl("https://zhaopin.meituan.com/api/official/job/getJobDetail",
             post={"jobUnionId": jid}, referer="https://zhaopin.meituan.com/web/position")
    brief("meituan-detail", d, 900)
except Exception as e:
    print("meituan parse fail", e)

time.sleep(1)
# ---- 百度记录全字段 ----
b = json.loads(curl("https://talent.baidu.com/httservice/getPostListNew",
                    form={"recruitType": "SOCIAL", "pageSize": 2, "keyWord": "Agent",
                          "curPage": 1, "projectType": "", "postType": "",
                          "workPlace": "", "bg": ""},
                    referer="https://talent.baidu.com/jobs/list"))
print("baidu keys:", list(b["data"]["list"][0].keys()))

# ---- 百度校园招聘 recruitType 取值 ----
for rt in ["校园招聘", "校招", "GRADUATE", "STUDENT", "CAMPUS"]:
    time.sleep(1)
    d = curl("https://talent.baidu.com/httservice/getPostListNew",
             form={"recruitType": rt, "pageSize": 2, "keyWord": "Agent", "curPage": 1,
                   "projectType": "", "postType": "", "workPlace": "", "bg": ""},
             referer="https://talent.baidu.com/jobs/list")
    try:
        jj = json.loads(d)
        print("baidu rt=", rt, jj.get("status"), (jj.get("data") or {}).get("total"))
    except Exception:
        brief("baidu-rt-" + rt, d, 120)

# ---- join.qq.com 校招站 ----
h = curl("https://join.qq.com/", save="joinqq.html")
print("join.qq.com len", len(h))
apis = sorted(set(re.findall(r'["\'](/api/[A-Za-z0-9_/\-]{3,60})["\']', h)))
print("join api hints:", apis[:30])
for u in ["https://join.qq.com/api/getPositionList?page=1&pageSize=5&keyword=Agent",
          "https://join.qq.com/api/position/list?pageNo=1&pageSize=5&keyword=Agent"]:
    time.sleep(1)
    brief("joinqq-api", curl(u, referer="https://join.qq.com/"), 200)
