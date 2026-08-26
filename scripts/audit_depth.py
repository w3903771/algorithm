"""章的深度分档 ＋ 知识点的三层覆盖判定，输出 dev/audit/知识点深度审计.md。

`audit_sources.py` 验的是**归属**：169 个知识点都有章节认领。
但「有章节认领」不等于「讲透了」——背包九讲那一例就是确证：
章首自述「把九种形态一次讲完」，实测 P08 泛化物品**全章 0 次出现**（01 号文件 §2）。

因此判定升级为三层（01 §一）：

| 层 | 判据 | 谁在管 |
| --- | --- | --- |
| **L1 认领** | 有章节声明承接，且那一章真的在磁盘上 | `audit_sources.py`，本脚本复核 |
| **L2 讲透** | 该章命中这条知识点登记的 `anchors` | **本脚本** |
| **L3 有题** | 该章有配套例题，且例题拿到过判定 | 本脚本（章级） |

`dev/data/_source_topics.json` 的条目因此从 `{"chapter": "..."}` 扩成：

    {"chapter": "dp/knapsack",
     "anchors": ["泛化物品", "最优方案总数"],   # 支持同义词：["SG 函数", "Sprague"] 写成嵌套数组
     "depth": "full",                          # full 全部命中才过 / brief 命中一条即过 / excluded 要写理由
     "note": "..."}

**anchors 支持同义词数组**（评审 R 条目要求）：`["SG 函数", ["折半", "meet in the middle"]]`
里嵌套的那一项只要命中其一即可。理由是关键词扫描有实测过的假阴性——
「SG 函数」在正文里写作 Sprague-Grundy，直接扫词会漏报（01 §4.0）。

**没登记 anchors 的条目单列一档，不算失败**：169 条里绝大多数还没登记，
那是 P1 的「逐条人工比对」要产出的东西（01 §三）。混进失败里会让这份报告没法看。

--------------------------------------------------------------------------
本脚本看不见什么
--------------------------------------------------------------------------
1. **讲得对不对、讲得够不够**。命中 anchor 只说明那个词出现过。
   「泛化物品」出现在一句「本章不讲泛化物品」里也算命中——anchors 是**筛子**，
   把「明显没讲」筛出来给人看，不是「讲透了」的证明。
2. **没登记 anchors 的那些知识点**。它们在本脚本里只有 L1 和 L3，L2 是空白。
   这一档的条数就是 P1 逐条比对的工作量。
3. **源资料本身**。`sources/` 不入库，本脚本不读它，只读 `_source_topics.json`
   这份已经人工整理过的清单——**清单漏了的知识点，这里也漏**。
4. **章的深度分档只看体量与结构**（字数、小节数、例题数、代码段数、有没有速查）。
   一章可以又长又空。分档是**排序用的**，不是质量判定。
5. **例题的正确性**。L3 只看「有没有例题、例题拿到过判定」，不重跑判题。
   跑样例归 `verify.py`，正文代码归 `verify_docs.py`。

用法: uv run python scripts/audit_depth.py
      uv run python scripts/audit_depth.py -v    # 打印每条知识点的三层判定
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
import check_prose  # noqa: E402   「什么算正文」的归口（front-matter 不算）

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DATA = ROOT / "data"        # 公开数据：站点构建与 check_prose 要读，随仓库发布
DEV_DATA = ROOT / "dev" / "data"   # 开发侧数据：不随本仓库发布，clone 的检出里没有这个目录
AUDIT = ROOT / "dev" / "audit"      # 脚本生成的报告：P-M② 起在 dev/audit/（02 §7.3）

REPORT = AUDIT / "知识点深度审计.md"

sys.path.insert(0, str(ROOT / "scripts"))
import sol_store  # noqa: E402


def chapter_path(cid: str) -> Path:
    return DOCS / (cid + ".md")


def chapter_text(cid: str) -> str | None:
    """章正文——**剥掉 front-matter**（09 教训二十二）。

    P1① 给 89 章补了 `id:` / `title:` 两行元信息。anchors 是「讲到什么程度才算讲透」
    的关键词，而一章的 anchor 十有八九就是它自己的标题——不剥的话
    `title: 线段树` 白送一个命中，L2 直接判「讲透」，正文一个字没讲也照样绿。
    今天只登记了 1 条 anchors 所以不发作，**风险面实测 52 条**
    （知识点名里含该章 title 的条目），P1②/P1③ 补完约 160 条 anchors 就会集中爆发。
    口径不在这里自己写，import `check_prose`（它是「什么算正文」的归口）。
    """
    p = chapter_path(cid)
    if not p.is_file():
        return None
    return check_prose.strip_front_matter(p.read_text(encoding="utf-8"))


def _line_kind(line: str) -> str:
    """这一行算哪一档正文。与 `check_prose` 的结构口径同源，只多分一个「引用块」。"""
    s = line.strip()
    if s.startswith("|"):
        return "表格"
    if s.startswith(">"):
        return "引用块"
    if s.startswith("#"):
        return "标题"
    return "正文"


def sieve_too_loose(body: str, anchor) -> bool:
    """这个 anchor 的命中是不是**全部**落在表格或章首「配套例题」块里。

    anchors 是筛子，而筛子有两个已知的漏法（09 教训十四 / 二十六）：
    一张汇总表能把好几个 anchor 一次全命中；章首那行「配套例题」列着题名，
    题名里含 anchor 词就白送一个命中。两者都让 L2 的 ✅ 变得不可信，
    而**报告里看不出来**——P1③ 锁定复核就是这么发现 `dp/basic` 的「坐标」
    只有章首例题块那一次命中的。

    **P-R① 之后第二个漏法自己消失了**：章首块改成构建期生成，源码里只剩一个
    注释 token，题名不再进正文，也就不会白送命中（实测 L2 六个数一个没动，
    说明它当时也确实没在撑着谁）。「引用块」这一类仍然拦着，因为正文里还有别的
    引用块；表格那一类不受影响。

    标题命中**算数**：`## 4　扩展欧几里得` 恰恰是「真讲开了」的强证据。
    """
    names = anchor if isinstance(anchor, list) else [anchor]
    kinds = {_line_kind(l) for l in body.splitlines() if any(n in l for n in names)}
    return bool(kinds) and kinds <= {"表格", "引用块"}


def hit(body: str, anchor) -> bool:
    """anchor 可以是字符串，也可以是同义词数组（命中其一即算）。"""
    if isinstance(anchor, list):
        return any(hit(body, a) for a in anchor)
    return anchor.lower() in body.lower()


# --------------------------------------------------------------- 章的深度分档

def chapter_stats(mapping: dict) -> list:
    """每章一行：字数、小节数、例题数、代码段数、有没有速查。

    分档只用来**排序**，判据写在这里而不是散在报告里：
    骨架（明确标了「状态：骨架 / 待扩写」，或正文不足 2000 字且小节 ≤ 2）·
    偏薄（不足 6000 字 或 无例题）· 常规（其余）。
    """
    out = []
    for cid in sorted(mapping):
        body = chapter_text(cid)
        if body is None:
            out.append(dict(id=cid, missing=True))
            continue
        # 先剥掉 HTML 注释再数：章首例题块 P-R① 起是两个 `<!-- CHAPTER-… -->` token
        # （04 §四 细节 3），把占位符算进字数，等于「把手写清单换成生成」这件事
        # 本身让每章凭空厚了几十字——那是与内容无关的量，会往「偏薄」的判据里注水。
        words = len(re.sub(r"\s", "", re.sub(r"<!--.*?-->", "", body, flags=re.S)))
        h2 = len(re.findall(r"^## ", body, re.M))
        code = len(re.findall(r"^```\w", body, re.M))
        probs = len(mapping[cid])
        declared = bool(re.search(r"状态：(骨架|待扩写)", body))
        if declared or (words < 2000 and h2 <= 2):
            tier = "骨架"
        elif words < 6000 or probs == 0:
            tier = "偏薄"
        else:
            tier = "常规"
        out.append(dict(id=cid, words=words, h2=h2, code=code, probs=probs,
                        tier=tier, declared=declared, missing=False))
    return out


# --------------------------------------------------------------- 知识点三层

def audit_topics(mapping: dict, tier_of: dict | None = None) -> tuple[list, dict]:
    src = json.loads((DEV_DATA / "_source_topics.json").read_text(encoding="utf-8"))
    metas = sol_store.load_all()
    judged = {no for no, m in metas.items()
              if ((m.get("langs") or {}).get("py") or {}).get("status")}

    rows = []
    for group, items in src.items():
        if group == "_comment":
            continue
        for topic, cfg in items.items():
            if cfg.get("excluded"):
                rows.append(dict(group=group, topic=topic, cid=None,
                                 l1="排除", l2="—", l3="—", miss=[], todo="",
                                 note=cfg["excluded"]))
                continue
            cid = cfg.get("chapter")
            body = chapter_text(cid) if cid else None
            l1 = "✅" if body is not None else ("❌ 章不存在" if cid else "❌ 未认领")

            anchors = cfg.get("anchors") or []
            depth = cfg.get("depth", "full")
            if not anchors:
                l2, miss = "· 未登记", []
            elif body is None:
                l2, miss = "❌", anchors
            else:
                miss = [a for a in anchors if not hit(body, a)]
                if depth == "brief":
                    l2 = "✅" if len(miss) < len(anchors) else "❌"
                else:
                    l2 = "✅" if not miss else "❌"

            probs = mapping.get(cid or "", [])
            if not probs:
                l3 = "❌ 无例题"
            elif any(p in judged for p in probs):
                l3 = "✅"
            else:
                l3 = "⚠ 例题未判定"
            loose = ([a for a in anchors if sieve_too_loose(body, a)]
                     if (anchors and body is not None) else [])
            rows.append(dict(group=group, topic=topic, cid=cid, l1=l1, l2=l2, l3=l3,
                             loose=loose,
                             miss=miss, todo=cfg.get("todo", ""),
                             note=cfg.get("note", ""),
                             anchors=anchors,
                             tier=(tier_of or {}).get(cid or "", "")))
    stat = {
        "总数": len(rows),
        "L1 通过": sum(r["l1"] == "✅" for r in rows),
        "L2 通过": sum(r["l2"] == "✅" for r in rows),
        # anchors 是筛子：一张汇总表就能把几个 anchor 全命中。
        # 「L2 说讲透了、章分档说这章偏薄」是两个判据在打架，单列出来盯着。
        "L2 通过但该章偏薄/骨架": sum(r["l2"] == "✅" and r.get("tier") in ("骨架", "偏薄")
                                   for r in rows),
        # 筛子太松：命中全部落在表格 / 章首例题块里，L2 的 ✅ 不可信（09 教训十四）
        "L2 命中全落在表格或引用块": sum(1 for r in rows if r.get("loose")),
        "L2 未登记 anchors": sum(r["l2"] == "· 未登记" for r in rows),
        "L2 失败（新问题）": sum(r["l2"] == "❌" and not r["todo"] for r in rows),
        "L2 失败（已排批次）": sum(bool(r["l2"] == "❌" and r["todo"]) for r in rows),
        "L3 通过": sum(r["l3"] == "✅" for r in rows),
        "排除": sum(r["l1"] == "排除" for r in rows),
    }
    return rows, stat


def main(argv: list) -> int:
    mapping = json.loads((DATA / "_mapping.json").read_text(encoding="utf-8"))["chapters"]
    chs = chapter_stats(mapping)
    tier_of = {c["id"]: ("缺文件" if c["missing"] else c["tier"]) for c in chs}
    rows, stat = audit_topics(mapping, tier_of)

    by_tier: dict = {}
    for c in chs:
        by_tier.setdefault("缺文件" if c["missing"] else c["tier"], []).append(c)

    AUDIT.mkdir(parents=True, exist_ok=True)
    L = ["# 知识点深度审计", "",
         "> 由 `scripts/audit_depth.py` 生成。**不要手改本文件。**", "",
         "`audit_sources.py` 验的是**归属**（有没有章节认领），这一份验的是**深度**。", "",
         "## 一、章的深度分档", "",
         "分档只看体量与结构，**用来排序，不是质量判定**（一章可以又长又空）。", "",
         "| 档 | 判据 | 章数 |", "| --- | --- | --- |",
         f"| 骨架 | 明确标了「状态：骨架 / 待扩写」，或正文 < 2000 字且 `##` 小节 ≤ 2 "
         f"| **{len(by_tier.get('骨架', []))}** |",
         f"| 偏薄 | 正文 < 6000 字，或一道配套例题都没有 | **{len(by_tier.get('偏薄', []))}** |",
         f"| 常规 | 其余 | **{len(by_tier.get('常规', []))}** |",
         f"| 缺文件 | `_mapping.json` 里有这一章，磁盘上没有 | **{len(by_tier.get('缺文件', []))}** |", ""]

    for tier in ("缺文件", "骨架", "偏薄"):
        items = by_tier.get(tier, [])
        if not items:
            continue
        L += [f"### {tier}（{len(items)} 章）", ""]
        if tier == "缺文件":
            L += [f"- `{c['id']}`" for c in items] + [""]
            continue
        L += ["| 章 | 字数 | `##` 小节 | 代码段 | 例题 | 自己标了状态 |",
              "| --- | --- | --- | --- | --- | --- |"]
        L += [f"| `{c['id']}` | {c['words']} | {c['h2']} | {c['code']} | {c['probs']} | "
              f"{'是' if c['declared'] else ''} |" for c in
              sorted(items, key=lambda x: x["words"])]
        L.append("")

    L += ["## 二、知识点的三层覆盖", "",
          "| 指标 | 条数 |", "| --- | --- |"]
    L += [f"| {k} | **{v}** |" for k, v in stat.items()]
    L += ["", "**「L2 未登记 anchors」不是失败**，是 P1 逐条人工比对要产出的东西"
          "（01 §三）：给每条知识点写下「讲到什么程度才算讲透」的那几个词。"
          "在那之前 L2 对这些条目是空白。", ""]

    bad2 = [r for r in rows if r["l2"] == "❌" and not r["todo"]]
    todo2 = [r for r in rows if r["l2"] == "❌" and r["todo"]]
    L += ["### L2 失败（登记了 anchors 却没命中）", "",
          "**新问题**——没有任何批次认领这个缺口。", ""]
    if bad2:
        L += ["| 知识点 | 章 | 缺的锚点 |", "| --- | --- | --- |"]
        L += [f"| {r['topic']} | `{r['cid']}` | "
              f"{'、'.join(str(a) for a in r['miss'])} |" for r in bad2]
    else:
        L.append("无。")
    thin2 = [r for r in rows if r["l2"] == "✅" and r.get("tier") in ("骨架", "偏薄")]
    L += ["", "### L2 说「讲透了」，章分档却说「偏薄 / 骨架」", "",
          "**两个判据在打架，这一节就是为了让它别被埋掉。**",
          "anchors 是**筛子**：它只问那几个词有没有出现，不问出现在哪种密度的正文里——",
          "一张汇总表就能把五个 anchor 一次全命中。所以 L2 的 ✅ 只能读作",
          "**「这些词都提到了」**，不能读作「这一章把它讲开了」。",
          "列在这里的条目要么补正文、要么把 anchors 换成只有真讲开了才命中的词。", ""]
    if thin2:
        L += ["| 知识点 | 章 | 章分档 | anchors |", "| --- | --- | --- | --- |"]
        L += [f"| {r['topic']} | `{r['cid']}` | **{r['tier']}** | "
              f"{'、'.join(str(a) for a in (r.get('anchors') or []))} |" for r in thin2]
    else:
        L.append("无。")

    loose2 = [r for r in rows if r.get("loose")]
    L += ["", "### L2 命中全部落在表格 / 引用块里（筛子太松）", "",
          "上面那一节问的是「章够不够厚」，这一节问的是**命中本身站不站得住**。",
          "一张汇总表能把好几个 anchor 一次全命中；章首那行「配套例题」列着题名，",
          "题名里含 anchor 词就白送一个命中——两种都让 L2 的 ✅ 变得不可信，",
          "而在别处**看不出来**。标题命中不算在内：`## 4　扩展欧几里得` 恰恰是讲开了的强证据。",
          "列在这里的条目要么补正文、要么换成只有真讲开了才命中的词（09 教训十四）。", ""]
    if loose2:
        L += ["| 知识点 | 章 | 站不住的 anchor | 已登记去向 |", "| --- | --- | --- | --- |"]
        L += [f"| {r['topic']} | `{r['cid']}` | "
              f"{'、'.join(str(a) for a in r['loose'])} | "
              f"{r['todo'] or ('见 note' if r.get('note') else '**未登记**')} |" for r in loose2]
    else:
        L.append("无。")

    L += ["", "### L2 缺口（已排进批次的已知待办）", ""]
    if todo2:
        L += ["| 知识点 | 章 | 缺的锚点 | 排在 |", "| --- | --- | --- | --- |"]
        L += [f"| {r['topic']} | `{r['cid']}` | "
              f"{'、'.join(str(a) for a in r['miss'])} | **{r['todo']}** |" for r in todo2]
    else:
        L.append("无。")
    L.append("")

    bad1 = [r for r in rows if r["l1"].startswith("❌")]
    L += ["### L1 失败（未认领，或认领的章不存在）", ""]
    L += (["| 知识点 | 声明的章 |", "| --- | --- |"]
          + [f"| {r['topic']} | `{r['cid']}` |" for r in bad1]) if bad1 else ["无。"]
    L.append("")

    bad3 = [r for r in rows if r["l3"].startswith("❌") and r["l1"] == "✅"]
    L += ["### L3 缺口（认领的章一道配套例题都没有）", "",
          "与 `audit_outline.py` 的「无例题 N 章」同源，是已登记待办（Q7 / P1② / P4 / P5）。", ""]
    if bad3:
        seen: dict = {}
        for r in bad3:
            seen.setdefault(r["cid"], []).append(r["topic"])
        L += ["| 章 | 落在这一章的知识点 |", "| --- | --- |"]
        L += [f"| `{c}` | {'、'.join(t)} |" for c, t in sorted(seen.items())]
    else:
        L.append("无。")
    L.append("")
    REPORT.write_text("\n".join(L), encoding="utf-8")

    if "-v" in argv:
        for r in rows:
            print(f"{r['l1']} {r['l2']} {r['l3']}  {r['topic']}  -> {r['cid']}")
    for r in bad2:
        print(f"[L2 失败] {r['topic']} @ {r['cid']}：缺 {r['miss']}")
    for r in todo2:
        print(f"[L2 已知待办 {r['todo']}] {r['topic']} @ {r['cid']}：缺 {r['miss']}")
    for r in bad1:
        print(f"[L1 失败] {r['topic']} -> {r['cid']}")

    print("　".join(f"{k} {v}" for k, v in stat.items()))
    print(f"章：骨架 {len(by_tier.get('骨架', []))}、偏薄 {len(by_tier.get('偏薄', []))}、"
          f"常规 {len(by_tier.get('常规', []))}")
    print(f"报告：{REPORT.relative_to(ROOT)}")
    return 1 if (bad1 or bad2) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
