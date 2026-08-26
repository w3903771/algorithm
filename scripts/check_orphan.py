"""逐题查「这道题在正文里被讲过没有」，输出 dev/audit/孤儿题核对.md。

**范围是磁盘上全部 366 题，不是 `_mapping.json` 里的 165 题。**
按「题在 `_mapping` 里但正文 0 引用」定义的话，201 道孤儿题根本不在 `_mapping` 里，
一条都报不出来——而它们正是这个脚本要抓的东西。

用每题 `meta.json` 的 `topics`（章节归属，`_mapping.json` 的反查）分三档：

| 档 | 判据 | 是什么 |
| --- | --- | --- |
| **甲** | 挂了章 ＋ 正文零引用 | **新问题**。章节归属声称讲了这道题，正文里却找不到它 |
| **乙** | 挂了章 ＋ 只在章首「配套例题」行出现 | **提示**。列了名字但正文没展开，P1② 决定是补讲还是撤归属。**P-R① 起结构上恒为 0**：章首块已改成构建期生成，源码里不再有那一行——这一档留着是为了拦「有人把手写清单写回去」 |
| **丙** | `topics` 为空 | **已知待办**。还没归属，不是闸门报错 |
| **丁** | 挂了章 ＋ 正文引用全在**别的**章里 | **提示**。归属声称这道题属于 A 章，讲它的却只有 B 章——归属与正文对不上，但甲档看不见（甲档只问「全库有没有被引用」）|

丙档现在是 201 条（BM 101 ＋ LC 100），是 08 号文件 §6.3 与 Q7 登记在册的待办。
**报告把「已知待办」与「新问题」分开列**——不分开的话，下一批看到 201 条会以为闸门坏了。

顺手做反向核对：**正文引用了却不存在的题号**。它和孤儿是同一次扫描的两端，
放一个脚本里比分给 `check_prose` 划算（`check_prose` 那边只留一句指向这里）。

--------------------------------------------------------------------------
本脚本看不见什么
--------------------------------------------------------------------------
1. **引用得对不对**。它只确认题号在正文里出现过，不确认那一段真的在讲这道题——
   「与 BISHI30 无关」这种否定式提及照样算命中。
2. **不带题号的引用**。正文若只写题名（「数楼梯那道题」）而不写题号，这里判它零引用。
   P1① 之后题号由渲染层展开、源码里仍写题号，所以这条盲区不会扩大。
3. **归属对不对**。`topics` 来自 `_mapping.json`，本脚本只拿它分档，不判断
   「这道题挂这一章合不合适」。那是 `audit_outline.py` 与人的活。
   丁档只查**位置**（讲它的章是不是它挂的章），不查**内容**。
4. **生成页里的引用**。附录 A 由 `gen_index.py` 生成、按构造包含每一道题，
   算进来的话没有一道题会是孤儿。凡带「自动生成」标记的页面整份跳过——
   代价是：**如果某天有人手写的正文被误标成生成页，它里面的引用也会一起看不见**。
5. **题解之间的互相引用**。只扫 `docs/`，不扫 `solutions/` 下的题解正文。
6. **`sources/` 与 `dev/`**。前者是原始资料、后者不发布，都不算「正文讲过」。

用法: uv run python scripts/check_orphan.py
      uv run python scripts/check_orphan.py -v    # 连各题的引用处一起打印
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DATA = ROOT / "data"        # 公开数据：站点构建与 check_prose 要读，随仓库发布
AUDIT = ROOT / "dev" / "audit"      # 脚本生成的报告：P-M② 起在 dev/audit/（02 §7.3）

REPORT = AUDIT / "孤儿题核对.md"

sys.path.insert(0, str(ROOT / "scripts"))
import sol_store  # noqa: E402

# 题号形如 BISHI30 / PIO7 / BM42 / LC1。
# 后面必须不是数字，否则 BISHI1 会在 BISHI100 里命中；
# 前面必须不是字母数字，否则 LC 会在 xxLC1 里命中。前缀表从注册表来，不写死。
def ref_pattern() -> re.Pattern:
    prefixes = sorted(sol_store.site_map(), key=len, reverse=True)
    return re.compile(r"(?<![A-Za-z0-9])(" + "|".join(prefixes) + r")(\d+)(?![0-9])")


GENERATED = re.compile(r"自动生成|不要手改")
HEADER_REF = re.compile(r"^\s*>?\s*\*\*配套例题\*\*")
EX_TOKENS = (re.compile(r"<!--\s*CHAPTER-EXAMPLES\s*-->"),
             re.compile(r"<!--\s*CHAPTER-EXAMPLE-TABLE\s*-->"))


def header_lag() -> tuple[list, list]:
    """有例题的章，是不是都带着章首那两个占位 token。

    **口径在 P-R① 换过一次。** 在那之前章首那行「配套例题」是**手写**的，
    这个函数数的是「它比 `_mapping.json` 落后多少个题号」——P1② 给 30 章挂了
    201 道题、一处都没往那行里加，于是它一直报「30 章落后 / 215 个题号」。
    P-R① 原子④ 按 04 §四 细节 3 把整块换成了构建期生成
    （`<!-- CHAPTER-EXAMPLES -->` ＋ `<!-- CHAPTER-EXAMPLE-TABLE -->`），
    手写的清单**一条都不剩**，那个计数天然归零。

    照 09 教训二十四：随欠账减少而变化的小节，走到头要有**显式的终止态**，
    否则它会退化成「83 个章都没有这一行」这种读起来像缺陷的噪声。
    所以这里改成问一件**新的、走到头也仍然成立**的事：
    **挂了例题的章，两个 token 一个都不许少。** 少一个，读者那一章就看不到清单，
    而没有任何别的闸门看得见——章首块不进 `check_links`（它不是链接）、
    不进 `check_prose`（它是注释）。

    仍然**不计入退出码**：新写的章在挂上例题、补上 token 之间会有一个窗口期，
    做成硬闸门会在「正在做对的事情」中途变红（09 教训二十三 / 二十五）。

    回 `(缺 token 的章, 手写清单的残留)`——后者应恒为空，非空就是有人写回去了。
    """
    mapping = json.loads((DATA / "_mapping.json").read_text(encoding="utf-8"))["chapters"]
    gap, legacy = [], []
    for cid, probs in sorted(mapping.items()):
        f = DOCS / (cid + ".md")
        if not f.is_file() or not probs:
            continue
        body = f.read_text(encoding="utf-8")
        miss = [n for n, pat in zip(("章首一句", "例题表"), EX_TOKENS)
                if not pat.search(body)]
        if miss:
            gap.append((cid, len(probs), miss))
        if any(HEADER_REF.match(l) for l in body.splitlines()):
            legacy.append((cid, len(probs)))
    return gap, legacy


def scan() -> tuple[dict, list, list]:
    """回 (题号 -> [(页, 行号, 是否章首配套例题行)], 跳过的生成页, 不存在的题号引用)。"""
    pat = ref_pattern()
    hits: dict = {}
    skipped, ghosts = [], []
    known = set(sol_store.all_numbers())

    for md in sorted(DOCS.rglob("*.md")):
        rel = md.relative_to(ROOT).as_posix()
        body = md.read_text(encoding="utf-8")
        # 生成页整份跳过：它按构造含每一道题，算进来就没有孤儿了
        if GENERATED.search("\n".join(body.splitlines()[:8])):
            skipped.append(rel)
            continue
        for i, line in enumerate(body.splitlines(), 1):
            in_header = bool(HEADER_REF.match(line))
            for m in pat.finditer(line):
                no = m.group(0)
                if no in known:
                    hits.setdefault(no, []).append((rel, i, in_header))
                else:
                    ghosts.append((no, rel, i))
    return hits, skipped, ghosts


def main() -> int:
    verbose = "-v" in sys.argv
    metas = sol_store.load_all()
    hits, skipped, ghosts = scan()

    tier_a, tier_b, tier_c, tier_d = [], [], [], []
    for no in sorted(metas, key=sol_store.sort_key):
        topics = metas[no].get("topics") or []
        refs = hits.get(no, [])
        real = [r for r in refs if not r[2]]
        if not topics:
            tier_c.append((no, len(refs)))
        elif not refs:
            tier_a.append((no, topics))
        elif not real:
            tier_b.append((no, topics, refs))
        else:
            # 丁档：正文里讲它的页，一个都不是它挂的章。
            # 页路径 docs/<id>.md 与章 id 一一对应（02 §3.2），所以直接比。
            own = {f"docs/{c}.md" for c in topics}
            if not any(pg in own for pg, _, _ in real):
                tier_d.append((no, topics, real))

    AUDIT.mkdir(parents=True, exist_ok=True)
    n_ref = sum(1 for no in metas if hits.get(no))
    out = ["# 孤儿题核对", "",
           "> 由 `scripts/check_orphan.py` 生成。**不要手改本文件。**", "",
           f"磁盘 **{len(metas)}** 题，正文引用到 **{n_ref}** 题。", "",
           "| 档 | 判据 | 条数 | 性质 |", "| --- | --- | --- | --- |",
           f"| 甲 | 挂了章 ＋ 正文零引用 | **{len(tier_a)}** | **新问题** |",
           f"| 乙 | 挂了章 ＋ 只在章首「配套例题」行出现 | **{len(tier_b)}** | 提示，P1② 定夺 |",
           f"| 丙 | `topics` 为空、尚未归属 | **{len(tier_c)}** | 已知待办（Q7 / P1②） |",
           f"| 丁 | 挂了章 ＋ 正文引用全在别的章 | **{len(tier_d)}** | 提示，归属与正文对不上 |",
           f"| — | 正文引用了却不存在的题号 | **{len(ghosts)}** | **新问题** |", ""]

    out += ["## 甲 · 挂了章却在正文零引用（新问题）", ""]
    if tier_a:
        out += ["| 题号 | 归属 |", "| --- | --- |"]
        out += [f"| {no} | {'、'.join(t)} |" for no, t in tier_a]
    else:
        out.append("无。")
    out.append("")

    out += ["## 乙 · 只在章首「配套例题」行出现（提示）", "",
            "章首那一行是归属清单，不是讲解。列在这里的题**正文没有展开**，",
            "P1② 归属时逐条定：补讲，还是把它从该章的例题里撤掉。", ""]
    if tier_b:
        out += ["| 题号 | 归属 | 出现在 |", "| --- | --- | --- |"]
        out += [f"| {no} | {'、'.join(t)} | {'、'.join(f'{p}:{ln}' for p, ln, _ in r[:3])} |"
                for no, t, r in tier_b]
    else:
        out.append("无。")
    out.append("")

    out += ["## 丁 · 挂了章，但正文只在别的章讲它（提示）", "",
            "归属说这道题属于 A 章，正文里讲它的却只有 B 章。两种情况都可能：",
            "**归属挂错了**，或者**该讲它的那一章还没写到它**。逐条定夺，别批量改。", ""]
    if tier_d:
        out += ["| 题号 | 归属 | 正文实际讲在哪 |", "| --- | --- | --- |"]
        out += [f"| {no} | {chr(12289).join(t_)} | {chr(12289).join(dict.fromkeys(pg for pg, _, _ in r))} |"
                for no, t_, r in tier_d]
    else:
        out.append("无。")
    out.append("")

    out += ["## 丙 · 尚未归属（已知待办，不是闸门报错）", "",
            f"**{len(tier_c)}** 题，登记在 08 号文件 §6.3 与 Q7：P1② 的归属会补掉一部分，",
            "其余随 P4 / P5 的新章补。**这一档归零之前，本脚本的退出码只看甲档与不存在的题号。**", ""]
    if tier_c:
        by_prefix: dict = {}
        for no, n in tier_c:
            by_prefix.setdefault(sol_store.prefix_of(no), []).append((no, n))
        out += ["| 题号前缀 | 条数 | 其中正文已提到 |", "| --- | --- | --- |"]
        for p, items in sorted(by_prefix.items()):
            out.append(f"| {p} | {len(items)} | {sum(1 for _, n in items if n)} |")
        out += ["", "<details><summary>逐条展开</summary>", "",
                "、".join(no for no, _ in tier_c), "", "</details>", ""]

    out += ["## 正文引用了却不存在的题号", ""]
    if ghosts:
        out += ["| 题号 | 出现在 |", "| --- | --- |"]
        out += [f"| {no} | {p}:{ln} |" for no, p, ln in ghosts]
    else:
        out.append("无。")
    gap, legacy = header_lag()
    out += ["", "## 章首例题块的占位 token（计数器，不计入退出码）", "",
            "章首那句「本章配套 N 道例题」与例题节开头那张表，"
            "**P-R① 原子④ 起由构建期生成**（04 §四 细节 3 的形态，用户 2026-08-25 拍板）：",
            "正文里只留两个 token，数字、题名、难度、链接全从 `_mapping.json` 与",
            "`_problems.json` 现算——手写等于给将来攒债（09 教训七）。",
            "",
            "**这一节问的是：挂了例题的章，两个 token 是不是都在。**",
            "少一个，读者那一章就看不到清单，而别的闸门都看不见它——",
            "章首块不是链接（`check_links` 不管），是注释（`check_prose` 不管）。",
            "",
            "> 本节的口径在 P-R① 换过一次。在那之前它数的是「手写那行比 `_mapping.json`",
            "> 落后多少个题号」（最后一次实测 30 章 / 215 个题号）。改成生成之后那个数",
            "> 天然归零，再留着就会退化成「83 个章都没有这一行」这种读起来像缺陷的噪声——",
            "> 随欠账减少而变化的小节，走到头要有显式的终止态（09 教训二十四）。",
            "",
            f"**{len(gap)} 个有例题的章缺 token；手写清单残留 {len(legacy)} 处。**", ""]
    if gap:
        out += ["| 章 | 挂着 | 缺哪个 |", "| --- | --- | --- |"]
        out += [f"| `{c}` | {n} 题 | {'、'.join(m)} |" for c, n, m in gap]
    else:
        out.append("无——有例题的章两个 token 全在。")
    if legacy:
        out += ["", "**还留着手写「配套例题」行的章**（应为空，非空就是有人写回去了）：",
                "、".join(f"`{c}`（{n} 题）" for c, n in legacy), ""]

    out += ["", "## 跳过的生成页", "",
            "这些页面带「自动生成」标记，按构造包含每一道题，算进来就不会有孤儿。", ""]
    out += [f"- `{s}`" for s in skipped] or ["无。"]
    out.append("")
    REPORT.write_text("\n".join(out), encoding="utf-8")

    if verbose:
        for no, t, r in tier_b:
            print(f"[乙] {no}（{'、'.join(t)}）：{r}")
    for no, t in tier_a:
        print(f"[甲] {no} 挂在 {'、'.join(t)}，正文零引用")
    for no, p, ln in ghosts:
        print(f"[题号不存在] {no} @ {p}:{ln}")

    print(f"\n甲 {len(tier_a)}（新问题）· 乙 {len(tier_b)}（提示）· 丁 {len(tier_d)}（提示）· "
          f"丙 {len(tier_c)}（已知待办）· 不存在的题号 {len(ghosts)}")
    print(f"报告：{REPORT.relative_to(ROOT)}")
    print(f"章首例题块 token：缺 {len(gap)} 章 · 手写残留 {len(legacy)} 处"
          f" —— 计数器，不计入退出码")
    return 1 if (tier_a or ghosts) else 0


if __name__ == "__main__":
    raise SystemExit(main())
