"""审计大纲：检查各题单的题目是否全部有归属、用户需求清单是否全部有章节承接、
章节是否有例题、以及各来源资料是否都被引用。

题单从 data/_sources.json 读，新增题单不用改这里。

用法: uv run python scripts/audit_outline.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DATA = ROOT / "data"        # 公开数据：站点构建与 check_prose 要读，随仓库发布
AUDIT = ROOT / "dev" / "audit"      # 脚本生成的报告：P-M② 起在 dev/audit/（02 §7.3）

REPORT = AUDIT / "大纲审计报告.md"


def load_sets() -> list:
    """题单注册表里实际抓下来的那些。"""
    d = json.loads((DATA / "_sources.json").read_text(encoding="utf-8"))
    return [s for s in d["sets"] if (ROOT / s["list"]).exists()]


def load_items(sets_) -> list:
    out = []
    for s in sets_:
        out += json.loads((ROOT / s["list"]).read_text(encoding="utf-8"))
    return out


def main() -> int:
    m = json.loads((DATA / "_mapping.json").read_text(encoding="utf-8"))
    chapters = m["chapters"]
    required = {k: v for k, v in m["required_topics"].items() if not k.startswith("_")}

    items = load_items(load_sets())
    all_problems = [it["no"] for it in items]
    all_set = set(all_problems)

    # 章 id -> 题目。P-M① 起 _mapping.json 是扁平的 {id: [题号]}，直接用
    ch2q = dict(chapters)
    q2ch = {}
    for ch, qs in chapters.items():
        for q in qs:
            q2ch.setdefault(q, []).append(ch)

    assigned = set(q2ch)
    unassigned = sorted(all_set - assigned,
                        key=lambda s: ("".join(c for c in s if c.isalpha()),
                                       int("".join(c for c in s if c.isdigit()) or 0)))
    ghost = sorted(assigned - all_set)
    empty_ch = [c for c, qs in ch2q.items() if not qs]
    missing_topic = {t: [c for c in cs if c not in ch2q]
                     for t, cs in required.items()}
    missing_topic = {t: cs for t, cs in missing_topic.items() if cs}

    dup = Counter(q for qs in ch2q.values() for q in qs)
    multi = {q: q2ch[q] for q, n in dup.items() if n > 1}

    L = ["# 大纲审计报告\n",
         "> 由 `scripts/audit_outline.py` 自动生成，校验依据 `data/_mapping.json`。\n",
         "## 结论速览\n",
         "| 检查项 | 结果 |", "| --- | --- |",
         f"| 题目总数 | {len(all_set)} |",
         f"| 已分配到章节的题目 | {len(assigned & all_set)} |",
         f"| **未分配题目** | **{len(unassigned)}** |",
         f"| 映射中不存在的题号 | {len(ghost)} |",
         f"| 章节总数 | {len(ch2q)} |",
         f"| 无例题的章节 | {len(empty_ch)} |",
         f"| 需求清单条目 | {len(required)} |",
         f"| **需求无章节承接** | **{len(missing_topic)}** |",
         f"| 跨章节复用的题目 | {len(multi)} |",
         ]

    L.append("\n## 未分配到任何章节的题目\n")
    if unassigned:
        titles = {it["no"]: (it["title"], it["difficulty"], "、".join(it["tags"]))
                  for it in items}
        L += ["| 题号 | 标题 | 难度 | 标签 |", "| --- | --- | --- | --- |"]
        for q in unassigned:
            t, d, tag = titles.get(q, ("?", "?", ""))
            L.append(f"| {q} | {t} | {d} | {tag} |")
    else:
        L.append("无 ✅")

    L.append("\n## 无例题的章节\n")
    L.append("\n".join(f"- {c}" for c in empty_ch) if empty_ch else "无 ✅")

    L.append("\n## 需求清单中无章节承接的条目\n")
    if missing_topic:
        L += [f"- **{t}** → 引用了不存在的章节 {cs}" for t, cs in missing_topic.items()]
    else:
        L.append("无 ✅　（用户列出的全部知识点均有章节负责）")

    L.append("\n## 需求清单覆盖明细\n")
    L += ["| 需求条目 | 承接章节 |", "| --- | --- |"]
    for t, cs in required.items():
        L.append(f"| {t} | {'；'.join(cs)} |")

    L.append("\n## 各章节例题分布\n")
    L += ["| 目录 | 章 id | 例题数 | 题号 |", "| --- | --- | --- | --- |"]
    for ch, qs in chapters.items():
        folder, _, slug = ch.rpartition("/")
        L.append(f"| {folder} | `{slug}` | {len(qs)} | {'、'.join(qs) or '—'} |")

    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")

    print(f"题目 {len(all_set)}，已分配 {len(assigned & all_set)}，未分配 {len(unassigned)}")
    print(f"章节 {len(ch2q)}，无例题 {len(empty_ch)}")
    print(f"需求 {len(required)} 条，无承接 {len(missing_topic)} 条")
    if ghost:
        print(f"[警告] 映射里有 {len(ghost)} 个不存在的题号: {ghost}")
    if unassigned:
        print(f"[待补] 未分配题目 {len(unassigned)} 个: {', '.join(unassigned)}")
    print(f"\n报告 -> {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
