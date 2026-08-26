"""审计 S2/S3/S4 三处本地资料的知识点是否都被大纲章节承接。

用法: uv run python scripts/audit_sources.py
输出: dev/audit/来源覆盖审计.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DATA = ROOT / "data"        # 公开数据：站点构建与 check_prose 要读，随仓库发布
DEV_DATA = ROOT / "dev" / "data"   # 开发侧数据：不随本仓库发布，clone 的检出里没有这个目录
AUDIT = ROOT / "dev" / "audit"      # 脚本生成的报告：P-M② 起在 dev/audit/（02 §7.3）
REPORT = AUDIT / "来源覆盖审计.md"

SRC_NAME = {
    "S2-cpp-algo-ds": "S2　C++ 算法与数据结构代码库",
    "S3-oi-courseware": "S3　信息学竞赛课件（2018级）day1–day10",
    "S4-pascal-template": "S4　Pascal 模板.docx（NOIP 复赛算法模板）",
}


def main() -> int:
    topics = json.loads((DEV_DATA / "_source_topics.json").read_text(encoding="utf-8"))
    mapping = json.loads((DATA / "_mapping.json").read_text(encoding="utf-8"))

    # P-M① 起 _mapping.json 与 _source_topics.json 都以章 id 为键
    known = set(mapping["chapters"])

    rows, missing, excluded, bad_ref = [], [], [], []
    for src, items in topics.items():
        if src.startswith("_"):
            continue
        for topic, info in items.items():
            if "excluded" in info:
                excluded.append((src, topic, info["excluded"]))
                continue
            ch = info.get("chapter")
            if not ch:
                missing.append((src, topic))
                continue
            if ch not in known:
                bad_ref.append((src, topic, ch))
            rows.append((src, topic, ch))

    total = len(rows) + len(missing) + len(excluded)
    L = ["# 来源资料覆盖审计（S2 / S3 / S4）\n",
         "> 由 `scripts/audit_sources.py` 自动生成，依据 `dev/data/_source_topics.json`。\n",
         "## 结论速览\n",
         "| 检查项 | 数量 |", "| --- | --- |",
         f"| 三处资料清点出的知识点 | {total} |",
         f"| 已有章节承接 | {len(rows)} |",
         f"| **未覆盖** | **{len(missing)}** |",
         f"| 明确排除（附理由） | {len(excluded)} |",
         f"| 指向不存在章节 | {len(bad_ref)} |",
         ]

    L.append("\n## 未覆盖的知识点\n")
    if missing:
        L += ["| 来源 | 知识点 |", "| --- | --- |"]
        L += [f"| {SRC_NAME.get(s, s)} | {t} |" for s, t in missing]
    else:
        L.append("无 ✅")

    if bad_ref:
        L.append("\n## 指向不存在章节（需修）\n")
        L += ["| 来源 | 知识点 | 引用章节 |", "| --- | --- | --- |"]
        L += [f"| {s} | {t} | `{c}` |" for s, t, c in bad_ref]

    L.append("\n## 明确排除的内容及理由\n")
    L += ["| 来源 | 知识点 | 排除理由 |", "| --- | --- | --- |"]
    L += [f"| {SRC_NAME.get(s, s)} | {t} | {r} |" for s, t, r in excluded]

    for src in topics:
        if src.startswith("_"):
            continue
        sub = [r for r in rows if r[0] == src]
        L.append(f"\n## {SRC_NAME.get(src, src)}　（{len(sub)} 个知识点）\n")
        L += ["| 知识点 | 承接章节 |", "| --- | --- |"]
        L += [f"| {t} | {c} |" for _, t, c in sub]

    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")

    print(f"知识点 {total}：已承接 {len(rows)}，未覆盖 {len(missing)}，明确排除 {len(excluded)}")
    if bad_ref:
        print(f"[错误] {len(bad_ref)} 个知识点指向不存在的章节:")
        for s, t, c in bad_ref:
            print(f"   {t} -> {c}")
    print(f"报告 -> {REPORT}")
    return 1 if (missing or bad_ref) else 0


if __name__ == "__main__":
    sys.exit(main())
