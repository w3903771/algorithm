"""提交结果的共享存储与报告渲染。

两个提交脚本（nc_submit 牛客、lc_submit 力扣）各写各的题号，
结果自 P-M③ 起落在**各题的** `meta.json` 的 `langs.py` 里
（原先是全局的 `solutions/_submit_results.json`），报告由这里统一渲染。
不这么做的话，谁后跑谁就把对方的 `_submit_report.md` 冲掉了。

报告格式要保持稳定：`hooks/build_pages.py` 靠 `| 题号 | 结果 |` 这一列
给题解页打「已 AC」标记，`scripts/gen_index.py` 靠它统计实测通过数。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sol_store as store  # noqa: E402

ROOT = store.ROOT
DOCS = ROOT / "docs"
DATA = store.DATA                   # 公开数据：见 sol_store.DATA
SOL = store.SOL
REPORT = SOL / "_submit_report.md"

_NUM = re.compile(r"^([A-Z]+)(\d+)$")

sort_key = store.sort_key


def load_results() -> dict:
    """`{题号: 判定}`，从各题的 meta.json 汇总。"""
    return store.submit_results()


def save_results(results: dict, changed: str = None) -> None:
    """写回各题的 meta.json。

    `changed` 点名这一轮刚判完的那道题时只写它一份——
    调用方是「提交一题、存一次」的循环，整表回写 366 份纯属浪费。
    """
    for no in ([changed] if changed else results):
        if no in results:
            store.save_submit_result(no, results[no])


def _sets() -> list:
    p = DATA / "_sources.json"
    if not p.exists():
        return []
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return [(s["prefix"], d["sites"].get(s["site"], {}).get("name", s["site"]), s["name"])
                for s in d["sets"]]
    except (ValueError, OSError, KeyError):
        return []


def render(results: dict = None) -> Path:
    """把累积的提交结果渲染成 `_submit_report.md`，按题单分节。"""
    results = load_results() if results is None else results
    ac = sum(1 for v in results.values() if v.get("status") == "AC")
    L = ["# 判题机提交结果\n",
         "> 由 `scripts/nc_submit.py`（牛客）与 `scripts/lc_submit.py`（力扣）生成，",
         "> 判定结果存在各题自己的 `meta.json` 里，报告在这里合并渲染。\n",
         f"**{ac} / {len(results)} 通过**\n"]

    grouped, seen = [], set()
    for prefix, site, name in _sets():
        keys = [k for k in results
                if _NUM.match(k) and _NUM.match(k).group(1) == prefix]
        if keys:
            grouped.append((f"{site} · {name}", sorted(keys, key=sort_key)))
            seen.update(keys)
    rest = sorted(set(results) - seen, key=sort_key)
    if rest:
        grouped.append(("其它", rest))

    for title, keys in grouped:
        n_ac = sum(1 for k in keys if results[k].get("status") == "AC")
        L += [f"## {title}\n", f"{n_ac} / {len(keys)} 通过\n",
              "| 题号 | 结果 | 判定 | 语言 |", "| --- | --- | --- | --- |"]
        for k in keys:
            v = results[k]
            icon = "✅ AC" if v.get("status") == "AC" else "❌ " + str(v.get("status"))
            L.append(f"| {k} | {icon} | {str(v.get('verdict', ''))[:120]} | {v.get('lang', '')} |")
        L.append("")

    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")
    return REPORT
