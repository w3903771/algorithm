#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""全库路径迁移：旧章路径 → 新 id 路径。

    uv run python scripts/migrate.py --dry     # 只报告，不落盘
    uv run python scripts/migrate.py --dry --verbose        # 逐行打印前后对比
    uv run python scripts/migrate.py --dry --only docs2sol  # 只看某一类
    uv run python scripts/migrate.py --apply   # 落盘：git mv ＋ 引用重写 ＋ 重定向表

映射表：`dev/_migration.json`（批次 P0a 产出，来源 02 号文件 §4）。
拆分章的目标 id 有多个，本脚本一律标 `SPLIT` 并取 `new[0]`——
P-M① 阶段这 9 章按原样整体迁到 `new[0]`，P-M② 再按 `dev/notes/拆分点.md` 切开。

落盘模式（`--apply`，P-M① 交付）做四件事，**一个字的正文都不改**：

1. `git mv` 74 章 ＋ 10 个部分索引 ＋ 3 篇附录到新 id 路径，`git rm` 唯一被删除的
   `docs/part10-进阶专题/index.md`（02 §2.2 修 B1，「进阶专题」整部解散）。
2. 重写 `docs/**/*.md` 与 `solutions/**/*.py` 里的相对引用。**只改路径**：
   链接文字、锚点、前后文一律原样保留（锚点另由 §5.4 人工复核）。
   目标不在本批次搬家的（`docs/00-*.md`、构建期生成的 `docs/solutions/*.md`、
   `docs/index.md`）也要重算相对深度——源文件的目录层数变了。
3. 重写两份数据文件里的章键：`docs/_mapping.json`（`部分/章名` → `目录/slug`）与
   `docs/_source_topics.json`（章名 → 新 id）。这两份文件本身留在原地，P-M② 才归位。
4. 生成 `dev/_redirects.yml`：`mkdocs-redirects` 的 `redirect_maps` 片段，旧 URL 301 到新 URL。

**不做**的事：`dev/` 归位与 `docs/00-*.md`（P-M②）、拆 9 个超载章（P-M②）、
`solutions/` 重组（P-M③，工具是 `scripts/migrate_solutions.py`）、
附录 A 与 `_problems.json` 里的章节显示名
（那是渲染层的旧章名，改了会让 366 个题解页全部产生内容差异，留给 P6 随索引层重写）。
"""
from __future__ import annotations

import argparse
import json
import posixpath
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIGRATION = ROOT / "dev" / "_migration.json"

# 02 号文件 §9.1 的实测数，用于核对本脚本扫到的量级
EXPECTED = {
    "docs2sol": 580,
    "docs2chap": 662,
    "sol2docs": 273,
    "scripts": 12,
}

# 硬编码旧路径的 12 个脚本（02 §9.1）
KNOWN_SCRIPTS = [
    "check_links", "corerun", "fix_solution_links", "gen_index", "lc_submit",
    "nc_fetch_template", "nc_submit", "new_solution", "submit_report",
    "test_corejudge", "verify", "verify_docs",
]

# ---------------------------------------------------------------- 映射表

class Mapping:
    """旧路径 ↔ 新 id 的双向查表。"""

    def __init__(self, data: dict):
        self.data = data
        self.by_old: dict[str, dict] = {}      # "docs/part3-数据结构/36-….md" -> entry
        self.by_base: dict[str, dict] = {}     # "36-哈希与字符串哈希.md"      -> entry
        self.by_no: dict[str, dict] = {}       # "36"                          -> entry

        for e in data["chapters"]:
            entry = {
                "old": e["old"],
                "new": e["new"],
                "split": e["kind"] == "split",
                "phase": e["phase"],
            }
            self.by_old[e["old"]] = entry
            self.by_base[posixpath.basename(e["old"])] = entry
            self.by_no[e["no"]] = entry

        for e in data["indexes"] + data["appendix"] + data.get("prose_fixups", []):
            entry = {"old": e["old"], "new": e["new"], "split": False, "phase": e["phase"]}
            self.by_old[e["old"]] = entry
            # index.md 的 basename 全库重名，不进 by_base

    def resolve(self, old_path: str):
        """旧的仓库相对路径 → entry；找不到返回 None。"""
        return self.by_old.get(old_path)

    def new_path(self, entry) -> str | None:
        """entry → 新的仓库相对路径 `docs/<id>.md`；被删除的页返回 None。"""
        if not entry["new"]:
            return None
        return "docs/%s.md" % entry["new"][0]


# ---------------------------------------------------------------- 扫描

LINK = re.compile(r"\]\(([^)\s]+?)(#[^)\s]*)?\)")
# 题解 .py 里裸写的 docs 路径，与 hooks/build_pages.py 的 _DOCS_PATH 同源。
# 不能只认 `docs/partN-…`：题解里也会引附录（BISHI147 引 C-Python竞赛避坑清单），
# 只匹配章目录会让附录引用漏网，迁移后变成指向已删文件的死路径。
RAW_DOCS_PATH = re.compile(r"docs/([^/\s]+)/([^\s，。、）」`\"']+)\.md")
# 脚本里硬编码的旧结构痕迹，两类：旧章路径 / 开发文档旧位置。
# 原本还有第三类「扁平 solutions 布局」（`_spj/`、`glob("*.py")`、`{no}.py`），
# 那是给 P-M③ 用的待办标记；P-M③ 已完成，留着只会把新写的
# sol_store.py / migrate_solutions.py 当成旧痕迹报出来，所以整类删掉。
HARDCODE = re.compile(
    r"part\d+-"                                              # 旧章目录
    r"|00-[^\"'\s]*\.md"                                     # docs/00-* 报告输出路径（→ dev/audit/）
    r"|_(problems|sources|mapping|source_topics)\.json"      # 数据文件（P-M② → dev/data/，P-S① 公开的那几份 → data/）
)


class Change:
    __slots__ = ("kind", "file", "lineno", "old", "new", "flag")

    def __init__(self, kind, file, lineno, old, new, flag=""):
        self.kind, self.file, self.lineno = kind, file, lineno
        self.old, self.new, self.flag = old, new, flag

    @property
    def changed(self) -> bool:
        """路径实际发生变化（同深度目录的相对链接可能原样不变）。"""
        return self.old != self.new


def iter_lines(path: Path):
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return
    for i, line in enumerate(text.splitlines(), 1):
        yield i, line


def rel_link(from_new_path: str, to_new_path: str) -> str:
    """两个新路径之间的 markdown 相对链接。"""
    return posixpath.relpath(to_new_path, posixpath.dirname(from_new_path))


def scan_docs(mp: Mapping) -> list[Change]:
    """docs/ 正文里的三类链接：→ 题解、→ 跨章、→ 附录/目录页。"""
    out = []
    for md in sorted((ROOT / "docs").rglob("*.md")):
        rel = md.relative_to(ROOT).as_posix()
        if posixpath.basename(rel).startswith("00-"):
            continue                                    # 开发文档，P-M② 单独处理
        entry = mp.resolve(rel)
        if entry is None:
            continue                                    # index.md 之外的未登记页（docs/index.md）
        src_new = mp.new_path(entry)
        if src_new is None:
            out.append(Change("deleted-page", rel, 0, rel, "(删除)", "DELETE"))
            continue
        src_dir = posixpath.dirname(rel)

        for lineno, line in iter_lines(md):
            for m in LINK.finditer(line):
                target, anchor = m.group(1), m.group(2) or ""
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                if not target.endswith(".md"):
                    continue

                abs_old = posixpath.normpath(posixpath.join(src_dir, target))
                flag = "ANCHOR" if anchor else ""

                # ① → 题解页
                if abs_old.startswith("docs/solutions/"):
                    new = rel_link(src_new, abs_old) + anchor
                    out.append(Change("docs2sol", rel, lineno,
                                      target + anchor, new, flag))
                    continue

                # ② / ③ → 章 / 附录 / 目录页
                tgt = mp.resolve(abs_old)
                if tgt is None:
                    if abs_old.startswith("docs/"):
                        out.append(Change("unmapped", rel, lineno,
                                          target + anchor, "?", "UNMAPPED"))
                    continue
                tgt_new = mp.new_path(tgt)
                if tgt_new is None:
                    out.append(Change("docs2chap", rel, lineno,
                                      target + anchor, "(目标页已删除)", "DELETE"))
                    continue
                if tgt["split"]:
                    flag = (flag + "|SPLIT").strip("|")
                kind = "docs2appendix" if "/appendix/" in abs_old else "docs2chap"
                out.append(Change(kind, rel, lineno, target + anchor,
                                  rel_link(src_new, tgt_new) + anchor, flag))
    return out


def scan_solutions(mp: Mapping) -> list[Change]:
    """solutions/*.py 里裸写的 `docs/partN-…/NN-….md`。"""
    out = []
    for py in sorted((ROOT / "solutions").rglob("*.py")):
        rel = py.relative_to(ROOT).as_posix()
        for lineno, line in iter_lines(py):
            for m in RAW_DOCS_PATH.finditer(line):
                old = m.group(0)
                entry = mp.resolve(old)
                if entry is None:
                    out.append(Change("sol2docs", rel, lineno, old, "?", "UNMAPPED"))
                    continue
                new = mp.new_path(entry)
                if new is None:
                    out.append(Change("sol2docs", rel, lineno, old, "(目标页已删除)", "DELETE"))
                    continue
                out.append(Change("sol2docs", rel, lineno, old, new,
                                  "SPLIT" if entry["split"] else ""))
    return out


def scan_scripts() -> list[Change]:
    """脚本 / hook / 配置里硬编码的旧结构。只报告，改造需人工。"""
    out = []
    targets = sorted((ROOT / "scripts").glob("*.py"))
    targets += sorted((ROOT / "hooks").glob("*.py"))
    targets += [ROOT / "mkdocs.yml", ROOT / "README.md"]
    for f in targets:
        if not f.exists():
            continue
        rel = f.relative_to(ROOT).as_posix()
        if rel == "scripts/migrate.py":
            continue
        for lineno, line in iter_lines(f):
            if HARDCODE.search(line):
                out.append(Change("hardcode", rel, lineno, line.strip()[:96], "(人工改造)", "MANUAL"))
    return out


# ---------------------------------------------------------------- 报告

def report(changes: list[Change], verbose: bool, only: str | None):
    by_kind = defaultdict(list)
    for c in changes:
        by_kind[c.kind].append(c)

    files_touched = {c.file for c in changes}
    hard_files = sorted({c.file for c in by_kind["hardcode"]})

    print("=" * 72)
    print("migrate.py --dry　待改清单")
    print("=" * 72)

    rows = [
        ("① docs/ → 题解链接",        "docs2sol",     EXPECTED["docs2sol"]),
        ("② docs/ → 跨章链接",        "docs2chap",    EXPECTED["docs2chap"]),
        ("③ docs/ → 附录链接",        "docs2appendix", None),
        ("④ solutions/*.py → 章路径", "sol2docs",     EXPECTED["sol2docs"]),
        ("⑤ 脚本/配置硬编码（行）",   "hardcode",     None),
        ("⑥ 未登记的目标（需人工）",  "unmapped",     0),
        ("⑦ 指向已删除页",            "deleted-page", None),
    ]
    print("\n%-24s %6s %6s %8s  %s" % ("类型", "扫到", "需改", "02 §9.1", "核对"))
    print("-" * 72)
    for label, kind, exp in rows:
        items = by_kind[kind]
        n, nc = len(items), sum(1 for c in items if c.changed)
        if exp is None:
            note = "—"
        elif n == exp:
            note = "✅ 吻合"
        else:
            note = "⚠ 差 %+d" % (n - exp)
        print("%-24s %6d %6d %8s  %s" % (label, n, nc, "—" if exp is None else exp, note))
    print("-" * 72)
    ref_kinds = ("docs2sol", "docs2chap", "docs2appendix", "sol2docs")
    print("%-24s %6d %6d" % (
        "合计引用",
        sum(len(by_kind[k]) for k in ref_kinds),
        sum(1 for k in ref_kinds for c in by_kind[k] if c.changed)))
    print("%-24s %6d" % ("涉及文件", len(files_touched)))
    print("%-24s %6d" % ("需人工改造的脚本/配置", len(hard_files)))
    print("\n注：「扫到」是引用总量（对齐 02 §9.1 的口径），「需改」是路径实际变化的条数——"
          "\n    新旧目录同为一级时相对链接原样不变（如 `../solutions/X.md`），这类不需改写。")

    # 脚本清单与 02 §9.1 点名的 12 个对照
    named = {"scripts/%s.py" % s for s in KNOWN_SCRIPTS}
    hit = sorted(f for f in hard_files if f in named)
    extra = sorted(f for f in hard_files if f not in named)
    print("\n需改造的脚本 / 配置：")
    print("  02 §9.1 点名且命中（%d/%d）：%s" % (len(hit), len(named),
                                                 ", ".join(Path(f).stem for f in hit) or "—"))
    miss = sorted(named - set(hard_files))
    if miss:
        print("  点名但本次未命中：%s" % ", ".join(Path(f).stem for f in miss))
    if extra:
        print("  额外命中（点名之外）：%s" % ", ".join(extra))

    # 风险标记
    flags = Counter(f for c in changes for f in c.flag.split("|") if f)
    if flags:
        print("\n风险标记：")
        for f, n in flags.most_common():
            desc = {
                "SPLIT": "目标是拆分章，P-M① 整体迁到 new[0]，P-M② 再按 split-points.md 切开",
                "ANCHOR":    "带 #锚点，章内标题编号会变，需逐条复核",
                "UNMAPPED":  "映射表里没有该目标，需人工补",
                "DELETE":    "目标页在新结构中被删除",
                "MANUAL":    "脚本/配置硬编码，不自动改写",
            }.get(f, "")
            print("  %-10s %5d  %s" % (f, n, desc))

    # 拆分章：待确认的归属
    amb_files = defaultdict(int)
    for c in changes:
        if "SPLIT" in c.flag:
            amb_files[c.old.split("#")[0]] += 1
    if amb_files:
        print("\n指向拆分章的引用（P-M① 全部落到 new[0]，P-M② 随拆章再分流）：")
        for tgt, n in sorted(amb_files.items(), key=lambda kv: -kv[1])[:15]:
            print("  %5d  %s" % (n, tgt))

    if verbose:
        print("\n" + "=" * 72)
        print("逐行前后对比")
        print("=" * 72)
        for kind, _, _ in [(k, 0, 0) for _, k, _ in rows]:
            if only and kind != only:
                continue
            items = by_kind[kind]
            if not items:
                continue
            print("\n--- %s（%d）---" % (kind, len(items)))
            for c in items:
                mark = ("  [%s]" % c.flag) if c.flag else ""
                print("  %s:%d\n    - %s\n    + %s%s" % (c.file, c.lineno, c.old, c.new, mark))

    print("\n未落盘。落盘模式是 P-M① 的交付物（09 号文件 §二 第 1 步）。")


# ---------------------------------------------------------------- 落盘

def build_plan(data) -> tuple:
    """→ (moves, removes, path_map)。

    `moves` 是 (旧仓库相对路径, 新仓库相对路径)；`removes` 是本批次删除的页；
    `path_map` 是**旧路径 → 新路径**的全量查表，链接重写只认它——
    查不到就说明目标本批次不搬家（`docs/00-*.md`、`docs/solutions/*.md`），
    保持原路径、只重算相对深度。

    拆分章在映射表里 `phase` 写的是 P-M②（拆开的时机），但**文件本身在 P-M① 就搬**，
    整章落到 `new[0]`，所以这里按「有没有 new」判断，不看 phase。
    """
    moves, removes, path_map = [], [], {}
    for group in ("chapters", "indexes", "appendix"):
        for e in data[group]:
            old = e["old"]
            if not e["new"]:
                removes.append(old)
                continue
            new = "docs/%s.md" % e["new"][0]
            path_map[old] = new
            if new != old:
                moves.append((old, new))
    return moves, removes, path_map


def rewrite_md(text: str, old_rel: str, new_rel: str, path_map: dict) -> str:
    """重写一份 markdown 里的相对链接。锚点与链接文字原样保留。"""
    old_dir = posixpath.dirname(old_rel)
    new_dir = posixpath.dirname(new_rel)

    def repl(m):
        target, anchor = m.group(1), m.group(2) or ""
        if target.startswith(("http://", "https://", "mailto:", "#")) or not target.endswith(".md"):
            return m.group(0)
        abs_old = posixpath.normpath(posixpath.join(old_dir, target))
        abs_new = path_map.get(abs_old, abs_old)
        return "](%s%s)" % (posixpath.relpath(abs_new, new_dir), anchor)

    return LINK.sub(repl, text)


def rewrite_py(text: str, path_map: dict) -> str:
    """题解里裸写的 `docs/partN-…/NN-….md` 换成新路径。"""
    return RAW_DOCS_PATH.sub(lambda m: path_map.get(m.group(0), m.group(0)), text)


def by_no(mp: "Mapping", chapter: str):
    """`112-连通性：强连通分量与割点` → `docs/graph/scc.md`；查不到返回 None。"""
    m = re.match(r"^(\d+)", chapter)
    entry = mp.by_no.get(m.group(1)) if m else None
    return "docs/%s.md" % entry["new"][0] if entry else None


def rewrite_data_files(mp: "Mapping", path_map: dict) -> list:
    """两份数据文件里的章键换成新 id。文件本身不搬家（P-M② 才归位）。"""
    touched = []

    # _mapping.json：{部分: {章名: [题号]}} → **扁平** {id: [题号]}
    # 扁平而不是「{目录: {slug: …}}」两级，有两个理由：
    #   ① 02 §3.2 说 id 是永久主键，_mapping.json 就该直接以它为键；
    #   ② 两级会按目录重排，而 hooks 里「讲解章节」那行是按本表的顺序渲染的，
    #      重排会平白改掉题解页上的章节次序——那是内容差异，本批次不许有。
    p = ROOT / "docs" / "_mapping.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    out = {}
    for part, chapters in data["chapters"].items():
        for chapter, problems in chapters.items():
            # 个别章名里的全角冒号在文件名里写成了连字符
            # （112-连通性：强连通分量与割点 vs 112-连通性-强连通分量与割点.md），
            # 所以按路径查不到时退回按章号查——章号是这两份数据里唯一稳定的键。
            new = path_map.get("docs/%s/%s.md" % (part, chapter)) or by_no(mp, chapter)
            if new is None:
                raise SystemExit("_mapping.json 里有未登记的章：%s/%s" % (part, chapter))
            out[new[len("docs/"):-len(".md")]] = problems
    data["chapters"] = out
    # required_topics 的值也是章名（["01-语法与执行模型", …]），同样换成 id
    for topic, names in data["required_topics"].items():
        if topic.startswith("_"):
            continue
        data["required_topics"][topic] = [
            (path_map.get("docs/%s.md" % n) or by_no(mp, n))[len("docs/"):-len(".md")]
            if by_no(mp, n) else n
            for n in names
        ]
    if "新 id" not in data["_comment"]:
        data["_comment"] = data["_comment"].replace(
            "章节定义", "章节定义（键为新 id，顺序即原章号顺序，P-M① 迁移后口径）")
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    touched.append(p.relative_to(ROOT).as_posix())

    # _source_topics.json：{"chapter": "30-序列与数组"} → {"chapter": "ds/array"}
    p = ROOT / "docs" / "_source_topics.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    for key, topics in data.items():
        if key.startswith("_"):
            continue
        for _, item in topics.items():
            name = item.get("chapter")
            if not name:
                continue
            entry = mp.by_base.get(name + ".md")
            new = entry["new"][0] if entry else (by_no(mp, name) or "")[len("docs/"):-len(".md")]
            if not new:
                raise SystemExit("_source_topics.json 里有未登记的章：%s" % name)
            item["chapter"] = new
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    touched.append(p.relative_to(ROOT).as_posix())
    return touched


# 重定向表由 `moves` 生成，而 `moves` 只含**被移动**的页面。
# 整部解散的 part10「进阶专题」还有一个目录索引页 `index.md`，它是**被删除**的——
# 9 章各回主题目录，没有单一后继页，于是它天然进不了 moves，也就没有重定向，
# 而它今天是线上的活 URL（P-R① 原子③ 比页面集合时抓到：`main` 456 页 → 合并后 558 页，
# 消失的恰好只有它一个）。指向首页：首页上就是全书章节盘，读者从那儿能找到这 9 章的任何一章。
_EXTRA_REDIRECTS = {"part10-进阶专题/index.md": "index.md"}


def write_redirects(moves: list) -> str:
    """`mkdocs-redirects` 的 redirect_maps 片段，供 mkdocs.yml 抄录。"""
    lines = ["# 由 scripts/migrate.py --apply 生成（P-M①）。",
             "# 旧 URL 301 到新 URL，02 号文件 §9.2 第 4 条要求保留至少一年。",
             "# 内容与 mkdocs.yml 的 plugins.redirects.redirect_maps 逐行一致。"]
    rows = {old[len("docs/"):]: new[len("docs/"):] for old, new in moves}
    rows.update(_EXTRA_REDIRECTS)
    for old, new in sorted(rows.items()):
        lines.append("%s: %s" % (old, new))
    out = ROOT / "dev" / "_redirects.yml"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out.relative_to(ROOT).as_posix()


def git(*args) -> None:
    r = subprocess.run(["git"] + list(args), cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit("git %s 失败：\n%s" % (" ".join(args), r.stderr or r.stdout))


def apply(mp: "Mapping", data: dict) -> int:
    r = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.stdout.strip():
        print("工作区不干净，先提交或暂存：\n" + r.stdout, file=sys.stderr)
        return 2

    moves, removes, path_map = build_plan(data)

    # ① 先把重写后的正文算出来（按旧路径读，按新路径的深度算相对链接），
    #    再搬家、再落盘。顺序反了就会拿旧目录去算新链接。
    pending = {}
    for md in sorted((ROOT / "docs").rglob("*.md")):
        rel = md.relative_to(ROOT).as_posix()
        if posixpath.basename(rel).startswith("00-"):
            continue                                    # 开发文档，P-M② 一起搬
        if rel in removes:
            continue
        new_rel = path_map.get(rel, rel)
        text = md.read_text(encoding="utf-8")
        new_text = rewrite_md(text, rel, new_rel, path_map)
        if new_text != text:
            pending[new_rel] = new_text

    for py in sorted((ROOT / "solutions").rglob("*.py")):
        rel = py.relative_to(ROOT).as_posix()
        text = py.read_text(encoding="utf-8")
        new_text = rewrite_py(text, path_map)
        if new_text != text:
            pending[rel] = new_text

    # ② git mv：目标目录先建出来，git mv 不会自己建
    for old, new in moves:
        (ROOT / new).parent.mkdir(parents=True, exist_ok=True)
        git("mv", old, new)
    for old in removes:
        git("rm", "-q", old)

    # ③ 落盘重写后的正文
    for rel, text in sorted(pending.items()):
        (ROOT / rel).write_text(text, encoding="utf-8")

    # ④ 数据文件与重定向表
    touched = rewrite_data_files(mp, path_map)
    redirects = write_redirects(moves)

    print("=" * 72)
    print("migrate.py --apply　已落盘")
    print("=" * 72)
    print("%-26s %4d" % ("git mv（章 / 索引 / 附录）", len(moves)))
    print("%-26s %4d" % ("git rm（本批次删除的页）", len(removes)))
    for old in removes:
        print("      %s" % old)
    print("%-26s %4d" % ("引用重写后落盘的文件", len(pending)))
    print("%-26s   %s" % ("数据文件章键重写", "、".join(touched)))
    print("%-26s   %s" % ("重定向表", redirects))
    print("\n下一步（09 号文件 §二）：第 2 步改 hooks/build_pages.py，第 3 步改脚本，"
          "\n第 4 步 mkdocs.yml nav ＋ redirects，第 5 步锚点复核，第 6–7 步验收。")
    return 0


def main():
    for stream in (sys.stdout, sys.stderr):        # Windows 控制台默认 GBK
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="全库路径迁移")
    ap.add_argument("--dry", action="store_true", help="只报告，不落盘")
    ap.add_argument("--apply", action="store_true",
                    help="落盘：git mv ＋ 引用重写 ＋ 重定向表")
    ap.add_argument("--verbose", "-v", action="store_true", help="逐行打印前后对比")
    ap.add_argument("--only", help="只看某一类：docs2sol / docs2chap / sol2docs / hardcode …")
    args = ap.parse_args()

    if not (args.dry or args.apply):
        ap.print_help()
        return 2

    if not MIGRATION.exists():
        print("缺少 %s" % MIGRATION, file=sys.stderr)
        return 2
    data = json.loads(MIGRATION.read_text(encoding="utf-8"))
    if not data.get("status", "").startswith("confirmed"):
        print("⚠ 映射表未确认：%s\n" % data.get("status", "(缺 status 字段)"))

    mp = Mapping(data)
    if args.apply:
        return apply(mp, data)
    changes = scan_docs(mp) + scan_solutions(mp) + scan_scripts()
    report(changes, args.verbose, args.only)
    return 0


if __name__ == "__main__":
    sys.exit(main())
