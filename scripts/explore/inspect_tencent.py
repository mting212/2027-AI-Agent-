# -*- coding: utf-8 -*-
import json, requests
requests.packages.urllib3.disable_warnings()
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}

base = "https://careers.tencent.com/tencentcareer/api/post/Query"
p1 = {"timestamp": "1700000000000", "countryId": "", "cityId": "", "bgIds": "",
      "productId": "", "categoryId": "", "parentCategoryId": "", "attrId": "",
      "keyword": "Agent", "pageIndex": 1, "pageSize": 20, "language": "zh-cn", "area": "cn"}
r = requests.get(base, params=p1, headers=H, timeout=20, verify=False)
d = r.json()
print("total:", d["Data"]["Count"], "keys:", list(d["Data"]["Posts"][0].keys()))
print(json.dumps(d["Data"]["Posts"][0], ensure_ascii=False, indent=1))
print("=== titles ===")
for p in d["Data"]["Posts"][:20]:
    print(p["LocationName"], "|", p["CategoryName"], "|", p["RecruitPostName"])

# detail api
pid = d["Data"]["Posts"][0]["PostId"]
rd = requests.get("https://careers.tencent.com/tencentcareer/api/post/ByPostId",
                  params={"postId": pid, "language": "zh-cn"}, headers=H, timeout=20, verify=False)
print("=== detail status", rd.status_code)
try:
    dd = rd.json()
    print(json.dumps(dd, ensure_ascii=False, indent=1)[:2500])
except Exception as e:
    print(rd.text[:500], e)
