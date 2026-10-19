# -*- coding: utf-8 -*-
"""用 GitHub API (gh CLI) 拉取候选项目真实指标 -> data/repos_raw.json"""
import json, subprocess, pathlib, time

OUT = pathlib.Path("data")
OUT.mkdir(exist_ok=True)
import repos as R

items = []
for row in R.R:
    full, cluster, terms, diff, hours, gpu, zh, pers, why, task, output, interview = row
    p = subprocess.run(["gh", "api", f"repos/{full}"], capture_output=True)
    txt = p.stdout.decode("utf-8", "replace")
    if p.returncode != 0 or not txt.strip():
        print("FAIL", full, txt[:120])
        items.append(dict(full_name=full, ok=False, cluster=cluster))
        continue
    d = json.loads(txt)
    lic = (d.get("license") or {}).get("spdx_id")
    items.append(dict(
        ok=True, full_name=full, name=d.get("name"), cluster=cluster, jd_terms=terms,
        difficulty=diff, hours=hours, gpu_required=gpu, zh_docs=zh, persuasion=pers,
        why=why, task=task, output=output, interview=interview,
        stars=d.get("stargazers_count"), forks=d.get("forks_count"),
        open_issues=d.get("open_issues_count"), watchers=d.get("subscribers_count"),
        created=d.get("created_at"), pushed=d.get("pushed_at"),
        license=lic, language=d.get("language"), archived=d.get("archived"),
        topics=d.get("topics") or [], description=d.get("description"),
        url=d.get("html_url"), size_kb=d.get("size"), has_issues=d.get("has_issues"),
    ))
    time.sleep(0.25)

with (OUT / "repos_raw.json").open("w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=1)
ok = [i for i in items if i["ok"]]
bad = [i for i in items if not i["ok"]]
print(f"ok={len(ok)} fail={len(bad)}")
print("fail:", [b["full_name"] for b in bad])
print("top stars:", [(i["full_name"], i["stars"]) for i in sorted(ok, key=lambda x: -(x["stars"] or 0))[:15]])
