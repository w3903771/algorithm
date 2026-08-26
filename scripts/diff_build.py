#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""迁移前后站点内容比对：确认「除路径外内容无差异」。

    uv run python scripts/diff_build.py --snapshot before   # 迁移前，在干净工作区跑
    …执行 scripts/migrate.py…
    uv run python scripts/diff_build.py --snapshot after    # 迁移后
    uv run python scripts/diff_build.py --compare           # 按映射表归一化后比对
    uv run python scripts/diff_build.py --compare -v        # 打印逐页文本 diff

为什么需要它（02 号文件 §9.2 第 5 条）：P-M① 要改约 1500 处引用，逐页人工 diff 不现实。
本脚本把两次 `mkdocs build` 的**正文渲染结果**抽出来，按 `dev/_migration.json` 归一化
页面路径与站内链接，再逐页比对——**应报告零内容差异**。任何非零差异都要逐条解释清楚
才允许提交 P-M①。

快照存放在 `.cache/diff_build/<name>/`（已 gitignore 的缓存目录，不进仓库）。
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "diff_build"
MIGRATION = ROOT / "dev" / "_migration.json"

# mkdocs-material 的正文容器；nav / header / footer / 搜索索引都不比
CONTENT_SELECTOR = "article.md-content__inner, .md-content__inner"
# 构建期注入、随 nav 走的块，不算内容差异：
#   .chapter-map  章节盘（`<!-- CHAPTER-MAP -->` 占位渲染而来）。它按 nav 的分组
#                 逐目录列「章号 · 标题 · N 题」，P-M① 把 74 章重新分了目录
#                 （part10「进阶专题」整部解散，各章回到主题目录），
#                 这张盘必然重排。它是导航产物，不是正文。
CONTENT_DROP = "nav, .md-source-file, .md-feedback, script, style, .chapter-map"
VOLATILE = re.compile(
    r"第\s*\d+\s*章"          # 章号由 nav 顺序生成
    r"|上一章|下一章"
    r"|共\s*\d+\s*章"
)
# mkdocs-redirects 生成的跳转壳子，不是页面
REDIRECT_STUB = re.compile(r'http-equiv=.{0,2}refresh', re.I)
WS = re.compile(r"[ \t ]+")


# ---------------------------------------------------------------- 快照

def build(site_dir: Path) -> None:
    if site_dir.exists():
        shutil.rmtree(site_dir)
    r = subprocess.run(
        ["uv", "run", "mkdocs", "build", "--site-dir", str(site_dir)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("[错误] mkdocs build 失败：\n" + (r.stderr or r.stdout), file=sys.stderr)
        sys.exit(1)


def extract(html: str) -> str:
    """HTML → 归一化的正文纯文本。"""
    soup = BeautifulSoup(html, "lxml")
    node = soup.select_one(CONTENT_SELECTOR)
    if node is None:
        return ""
    for tag in node.select(CONTENT_DROP):
        tag.decompose()
    lines = []
    for raw in node.get_text("\n").splitlines():
        line = WS.sub(" ", raw).strip()
        if not line or VOLATILE.search(line):
            continue
        lines.append(line)
    return "\n".join(lines)


def snapshot(name: str) -> None:
    site = CACHE / ("_site_" + name)
    out = CACHE / name
    print("构建站点 → %s" % site)
    build(site)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    pages = {}
    stubs = 0
    for html in sorted(site.rglob("index.html")):
        text = html.read_text(encoding="utf-8")
        if REDIRECT_STUB.search(text):
            stubs += 1                                 # 旧 URL 的 301 壳子，不是页面
            continue
        rel = html.parent.relative_to(site).as_posix()
        rel = "index" if rel == "." else rel
        pages[rel] = extract(text)
    (out / "pages.json").write_text(
        json.dumps(pages, ensure_ascii=False, indent=1), encoding="utf-8")
    shutil.rmtree(site)
    print("快照 %s：%d 页（另有 %d 个重定向壳子已跳过）→ %s"
          % (name, len(pages), stubs, out / "pages.json"))


# ---------------------------------------------------------------- 比对

def _site_path(rel: str) -> str:
    """`docs/x/y.md` 或 `x/y` → 站内目录式 URL 路径。"""
    if rel.startswith("docs/"):
        rel = rel[len("docs/"):]
    if rel.endswith(".md"):
        rel = rel[: -len(".md")]
    return rel[: -len("/index")] if rel.endswith("/index") else rel


def deleted_pages() -> set:
    """映射表里 `new` 为空的页——**声明要删的**，不是迁丢的。

    目前只有 `docs/part10-进阶专题/index.md` 一页：「进阶专题」整部解散
    （02 §2.2 修 B1），九章各自回到主题目录，这一页不重定向到任何单页。
    """
    data = json.loads(MIGRATION.read_text(encoding="utf-8"))
    return {_site_path(e["old"])
            for e in data["chapters"] + data["indexes"] + data["appendix"]
            if not e["new"]}


def url_map() -> dict[str, str]:
    """旧站内路径 → 新站内路径（不含 .md，mkdocs 的目录式 URL）。"""
    data = json.loads(MIGRATION.read_text(encoding="utf-8"))
    m = {}
    for e in data["chapters"] + data["indexes"] + data["appendix"]:
        old = e["old"][len("docs/"):-len(".md")]
        if old.endswith("/index"):
            old = old[: -len("/index")]
        if not e["new"]:
            continue
        new = e["new"][0]
        if new.endswith("/index"):
            new = new[: -len("/index")]
        m[old] = new
    return m


NAV_ROW = re.compile(r"^\s+- (.+?): (\S+\.md)\s*$")


def label_map() -> dict:
    """题解页里**构建期注入**的章节链接文字：旧文件名 → 新标题。

    `hooks/build_pages.py` 的 `_link_chapters` 把题解文档字符串里裸写的章路径
    渲染成站内链接。迁移前链接文字是旧文件名词干（`30-序列与数组`），
    迁移后是该章的中文标题（`序列与数组`，取自 nav 标签）——
    **变的是路径带来的显示名，不是任何一个字的正文**，
    和 `url_map()` 归一化页面路径是同一件事，所以在这里一并归一化。

    键 = `_migration.json` 的 `no` + `title`（正是旧文件名的词干）；
    值 = `mkdocs.yml` nav 标签去掉章号后的标题（正是 `_split_label` 的产物）。
    只对题解页生效：章节正文里的 `[30-序列与数组](…)` 是作者写的链接文字，
    P-M① 一个字没动，两边本来就一样，在那里做替换反而会凭空造出差异。
    """
    nav, in_nav = {}, False
    for line in (ROOT / "mkdocs.yml").read_text(encoding="utf-8").splitlines():
        if line.rstrip() == "nav:":
            in_nav = True
            continue
        if not in_nav:
            continue
        m = NAV_ROW.match(line)
        if m:
            nav[m.group(2)] = m.group(1)
    data = json.loads(MIGRATION.read_text(encoding="utf-8"))
    out = {}
    for e in data["chapters"]:
        label = nav.get(e["new"][0] + ".md", "")
        m = re.match(r"^\s*\d+\s*·\s*(.+)$", label)
        if m:
            out["%s-%s" % (e["no"], e["title"])] = m.group(1)
    return out


def raw_path_map() -> dict:
    """题解正文里**裸写**的仓库路径：旧 → 新。

    题解文档字符串里有「详见 docs/appendix/C-Python竞赛避坑清单.md 的……」这种写法。
    `hooks/build_pages.py` 只把**章**路径渲染成链接，附录路径原样留在正文里，
    所以它是以纯文本形式出现在页面上的。迁移把文件改了名，这行文本必然跟着变——
    仍然是「路径变了」，和 url_map()、label_map() 同类，一并归一化。
    """
    data = json.loads(MIGRATION.read_text(encoding="utf-8"))
    out = {}
    for e in data["chapters"] + data["indexes"] + data["appendix"]:
        if e["new"]:
            out[e["old"]] = "docs/%s.md" % e["new"][0]
    return out


def normalize_labels(path: str, text: str, labels: dict, paths: dict) -> str:
    """只对题解页生效：章节正文里的同名文字是作者写的，P-M① 一个字没动。"""
    if not path.startswith("solutions/"):
        return text
    for old, new in paths.items():
        if old in text:
            text = text.replace(old, new)
    for old, new in labels.items():
        if old in text:
            text = text.replace(old, new)
    return text


def compare(verbose: bool, limit: int) -> int:
    before = json.loads((CACHE / "before" / "pages.json").read_text(encoding="utf-8"))
    after = json.loads((CACHE / "after" / "pages.json").read_text(encoding="utf-8"))
    m = url_map()
    labels = label_map()
    paths = raw_path_map()

    renamed = {m.get(k, k): k for k in before}          # 新路径 → 旧路径
    unmoved = set(before) & set(after)

    expected_gone = deleted_pages()
    missing = [new for new in renamed
               if new not in after and new not in expected_gone]
    deleted = sorted(p for p in expected_gone if p in before)
    added = [k for k in after if k not in renamed and k not in unmoved]

    diffs = []
    for new_path, old_path in sorted(renamed.items()):
        if new_path not in after:
            continue
        a = normalize_labels(new_path, before[old_path], labels, paths)
        b = after[new_path]
        if a != b:
            diffs.append((old_path, new_path, a, b))

    print("=" * 72)
    print("diff_build --compare")
    print("=" * 72)
    print("迁移前页数        %d" % len(before))
    print("迁移后页数        %d" % len(after))
    print("按映射表配上对的  %d" % sum(1 for k in renamed if k in after))
    print("按映射表删除的页  %d（预期）" % len(deleted))
    for p in deleted:
        print("    %s" % p)
    print("丢失的页          %d" % len(missing))
    print("新增的页          %d" % len(added))
    print("内容有差异的页    %d" % len(diffs))
    print("题解页归一化      章节链接文字 %d 条、裸写路径 %d 条"
          % (len(labels), len(paths)))

    for label, items in (("丢失", missing), ("新增", added)):
        if items:
            print("\n%s的页：" % label)
            for p in sorted(items)[:limit]:
                extra = "  ← 原 %s" % renamed[p] if p in renamed else ""
                print("  %s%s" % (p, extra))
            if len(items) > limit:
                print("  …另有 %d 条" % (len(items) - limit))

    if diffs:
        print("\n内容有差异的页：")
        for old_path, new_path, a, b in diffs[:limit]:
            la, lb = a.splitlines(), b.splitlines()
            print("  %s → %s（%d → %d 行）" % (old_path, new_path, len(la), len(lb)))
            if verbose:
                for line in list(difflib.unified_diff(
                        la, lb, fromfile=old_path, tofile=new_path, lineterm="", n=1))[:60]:
                    print("    " + line)
        if len(diffs) > limit:
            print("  …另有 %d 页" % (len(diffs) - limit))

    ok = not (missing or added or diffs)
    print("\n%s" % ("✅ 零内容差异，P-M① 可以提交。"
                    if ok else
                    "❌ 存在差异。每一条都必须能解释清楚，否则不得提交 P-M①。"))
    return 0 if ok else 1


def main() -> int:
    for stream in (sys.stdout, sys.stderr):        # Windows 控制台默认 GBK
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="迁移前后站点内容比对")
    ap.add_argument("--snapshot", metavar="NAME", help="构建并存快照，通常是 before / after")
    ap.add_argument("--compare", action="store_true", help="比对 before 与 after")
    ap.add_argument("--verbose", "-v", action="store_true", help="打印逐页文本 diff")
    ap.add_argument("--limit", type=int, default=20, help="每类最多列出多少条（默认 20）")
    args = ap.parse_args()

    CACHE.mkdir(parents=True, exist_ok=True)
    if args.snapshot:
        snapshot(args.snapshot)
        return 0
    if args.compare:
        for name in ("before", "after"):
            if not (CACHE / name / "pages.json").exists():
                print("缺少快照 %s，先跑 --snapshot %s" % (name, name), file=sys.stderr)
                return 2
        return compare(args.verbose, args.limit)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
