"""抓取牛客题单清单 -> sources/05-nowcoder/<slug>_list.json / .md

题单来自 https://www.nowcoder.com/exam/oj?questionJobId=10&subTabName=online_coding_page
  topicId=389  笔试模板必刷    BISHI1~BISHI147   ACM 模式
  topicId=372  输入输出练习    PIO1~PIO18        ACM 模式
  topicId=295  面试必刷TOP101  BM1~BM101         核心代码模式

三个题单挂在同一个 questionJobId 下，走同一个接口，加一行配置即可。
题号（BISHI/PIO/BM）是牛客自己的 questionNo，不是本仓库编的，所以天然不冲突。

用法:
  uv run python scripts/nc_fetch_list.py          # 三个题单全抓
  uv run python scripts/nc_fetch_list.py bm       # 只抓指定 slug
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nc_common import SESSION  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "sources" / "05-nowcoder"
OUT.mkdir(parents=True, exist_ok=True)

API = "https://www.nowcoder.com/api/questiontraining/coding/getTopicQuestion"
DIFF = {1: "入门", 2: "简单", 3: "中等", 4: "较难", 5: "困难"}

TOPICS = [
    (389, "bishi", "笔试模板必刷"),
    (372, "pio", "输入输出练习"),
    (295, "bm", "面试必刷TOP101"),
]

SESSION.headers.update({
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.nowcoder.com/exam/oj?questionJobId=10&subTabName=online_coding_page",
    "X-Requested-With": "XMLHttpRequest",
})


def fetch_topic(topic_id: int) -> list:
    out, page = [], 1
    while True:
        r = SESSION.get(API, params={"questionJobId": 10, "topicId": topic_id,
                                     "page": page, "pageSize": 50}, timeout=40)
        j = r.json()
        if j.get("code") != 0:
            print("  [err]", j)
            break
        data = j["data"]
        qs = data.get("questions", [])
        out.extend(qs)
        total = data.get("totalPage", 1)
        print(f"  page {page}/{total} +{len(qs)} (累计 {len(out)})")
        if page >= total or not qs:
            break
        page += 1
        time.sleep(1.0)
    return out


def normalize(qs: list) -> list:
    items = []
    for q in qs:
        items.append({
            "no": q.get("questionNo"),
            "title": q.get("questionTitle"),
            "questionId": q.get("questionId"),
            "uuid": q.get("questionUUid"),
            "tpId": q.get("tpId"),
            "difficulty": DIFF.get(q.get("difficulty"), str(q.get("difficulty"))),
            "acceptRate": round(q.get("acceptRate") or 0, 2),
            "tags": [t.get("name") for t in (q.get("tags") or [])],
            "url": f"https://www.nowcoder.com/practice/{q.get('questionUUid')}",
        })
    items.sort(key=lambda it: int(re.sub(r"\D", "", it["no"] or "0") or 0))
    return items


def main(argv=()) -> int:
    only = set(argv[1:])
    summary = []
    for topic_id, slug, name in TOPICS:
        if only and slug not in only:
            continue
        print(f"\n== {name} (topicId={topic_id})")
        items = normalize(fetch_topic(topic_id))
        (OUT / f"{slug}_list.json").write_text(
            json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        lines = [f"# 牛客 {name} 题目清单\n",
                 f"> topicId={topic_id}，共 {len(items)} 题  ",
                 "> 入口: https://www.nowcoder.com/exam/oj?questionJobId=10&subTabName=online_coding_page\n",
                 "| 编号 | 题目 | 难度 | 通过率 | 标签 | 链接 |",
                 "| --- | --- | --- | --- | --- | --- |"]
        for it in items:
            lines.append(f"| {it['no']} | {it['title']} | {it['difficulty']} | {it['acceptRate']}% | "
                         f"{'、'.join(it['tags'])} | [练习]({it['url']}) |")
        (OUT / f"{slug}_list.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"  -> {len(items)} 题 写入 {slug}_list.json/.md")
        summary.append((name, slug, len(items)))

    print("\n汇总:")
    for name, slug, n in summary:
        print(f"  {name:<14} {n:>4} 题  ({slug})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
