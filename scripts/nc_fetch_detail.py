"""抓取牛客题目详情（题面/输入输出描述/样例）-> sources/05-nowcoder/problems/

用法:
  uv run python scripts/nc_fetch_detail.py            # 抓全部（bishi + pio + bm）
  uv run python scripts/nc_fetch_detail.py bishi 1 20 # 只抓 bishi 的第 1..20 题
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nc_common import get  # noqa: E402
from nc_html2md import parse_subject  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
NC = ROOT / "sources" / "05-nowcoder"
RAW = NC / "raw"
MD = NC / "problems"
RAW.mkdir(parents=True, exist_ok=True)
MD.mkdir(parents=True, exist_ok=True)

SETS = {"bishi": "笔试模板必刷", "pio": "输入输出练习", "bm": "面试必刷TOP101"}


def to_md(meta: dict, d: dict) -> str:
    L = [f"# {meta['no']} {d.get('title') or meta['title']}\n",
         f"> 来源: [{meta['url']}]({meta['url']})  ",
         f"> 难度: {meta['difficulty']}　通过率: {meta['acceptRate']}%　"
         f"标签: {'、'.join(meta['tags']) or '无'}  "]
    if d.get("limits"):
        L.append(f"> {d['limits']}  ")
    L.append("\n## 题目描述\n")
    L.append(d.get("description") or "_(未抓到)_")
    if d.get("inputDesc"):
        L.append("\n## 输入描述\n")
        L.append(d["inputDesc"])
    if d.get("outputDesc"):
        L.append("\n## 输出描述\n")
        L.append(d["outputDesc"])
    for k, v in (d.get("otherDesc") or {}).items():
        L.append(f"\n## {k}\n")
        L.append(v)
    for ex in d.get("examples") or []:
        L.append(f"\n## {ex['name']}\n")
        L.append("**输入**\n")
        L.append("```\n" + ex["input"] + "\n```\n")
        L.append("**输出**\n")
        L.append("```\n" + ex["output"] + "\n```")
        if ex.get("note"):
            L.append("\n**说明**\n")
            L.append(ex["note"])
    return "\n".join(L) + "\n"


def run(slug: str, lo: int = 0, hi: int = 10 ** 9) -> tuple:
    items = json.loads((NC / f"{slug}_list.json").read_text(encoding="utf-8"))
    ok = fail = skip = 0
    for i, meta in enumerate(items, 1):
        if not (lo <= i <= hi):
            continue
        raw_p = RAW / f"{meta['no']}.json"
        if raw_p.exists():
            skip += 1
            continue
        url = f"https://www.nowcoder.com/questionTerminal/{meta['uuid']}"
        html = get(url)
        d = parse_subject(html) if html else {}
        if not d or not (d.get("description") or d.get("examples")):
            print(f"  [FAIL] {meta['no']} {meta['title']}  (html={len(html)})")
            fail += 1
            continue
        d["meta"] = meta
        raw_p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        (MD / f"{meta['no']}.md").write_text(to_md(meta, d), encoding="utf-8")
        ok += 1
        if ok % 10 == 0:
            print(f"  ... {slug} 已抓 {ok} 题 (最新 {meta['no']} {meta['title']})")
    print(f"[{slug}] 成功 {ok}，跳过(已存在) {skip}，失败 {fail}")
    return ok, skip, fail


def main(argv) -> int:
    if len(argv) >= 2:
        slug = argv[1]
        lo = int(argv[2]) if len(argv) > 2 else 0
        hi = int(argv[3]) if len(argv) > 3 else 10 ** 9
        run(slug, lo, hi)
    else:
        for slug in SETS:
            print(f"\n== {SETS[slug]} ({slug})")
            run(slug)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
