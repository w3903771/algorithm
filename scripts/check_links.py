"""校验（并可自动修复）教程内部的相对链接与 #锚点。

MkDocs 的锚点由标题文本 slugify 而来，手写跨章节链接很容易和实际锚点差一两个字符。

**锚点以构建产物为准**：直接从 `mkdocs build` 生成的 HTML 里读 `id=` 属性，
而不是自己重算 slug——pymdownx 的 slugify 直接调用与经 toc 扩展调用对全角空格的处理
并不一致（前者丢弃、后者转成分隔符），自己重算会漏报。

用法:
  uv run python scripts/check_links.py          # 只报告（会先构建站点）
  uv run python scripts/check_links.py --fix    # 唯一匹配的自动改正
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
AUDIT = ROOT / "dev" / "audit"      # 脚本生成的报告：P-M② 起在 dev/audit/（02 §7.3）
REPORT = AUDIT / "链接校验报告.md"

# 只看 Markdown 行内链接，跳过代码块
LINK = re.compile(r"\[(?:[^\]]*)\]\(([^)\s]+)\)")
FENCE = re.compile(r"^\s*```")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


SITE = ROOT / "_site_check"
ID_ATTR = re.compile(r'<h[1-6][^>]*\sid="([^"]+)"')


def build_site() -> bool:
    """跑一次 mkdocs build，把锚点的唯一权威来源准备好。"""
    import shutil
    import subprocess
    if SITE.exists():
        shutil.rmtree(SITE)
    # text=True 会用本地编码解 mkdocs 的输出，Windows 上默认 GBK，
    # 而 mkdocs 打印的是 UTF-8（含中文文件名与带重音的提示），会抛
    # UnicodeDecodeError 把真正的构建错误盖掉。显式指定编码并容错。
    r = subprocess.run(["uv", "run", "mkdocs", "build", "--site-dir", SITE.name],
                       cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("[错误] mkdocs build 失败：")
        print((r.stderr or r.stdout)[-1500:])
        return False
    return True


def anchors_from_site() -> dict:
    """docs 相对路径 -> 该页实际生成的锚点集合。"""
    out = {}
    for html in SITE.rglob("index.html"):
        rel = html.parent.relative_to(SITE).as_posix()
        key = "index.md" if rel == "." else rel + ".md"
        out[key] = set(ID_ATTR.findall(html.read_text(encoding="utf-8")))
    return out


def strip_md(text: str) -> str:
    """标题里的 Markdown 标记不进入锚点文本。"""
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\*\*([^*]*)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]*)\*", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\$([^$]*)\$", r"\1", text)
    return text


def anchors_of(path: Path) -> set:
    out, in_fence = set(), False
    for line in path.read_text(encoding="utf-8").split("\n"):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING.match(line)
        if m:
            out.add(slugify(strip_md(m.group(2))))
    return out


def iter_links(path: Path):
    in_fence = False
    for lineno, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in LINK.finditer(line):
            yield lineno, m.group(1)


def main(argv) -> int:
    fix = "--fix" in argv
    if not build_site():
        return 2
    site_anchors = anchors_from_site()
    md_files = sorted(p for p in DOCS.rglob("*.md") if not p.name.startswith("00-"))
    anchor_cache = {}
    for p in md_files:
        rel = p.relative_to(DOCS).as_posix()
        key = rel if rel == "index.md" else rel[:-3] + ".md"
        anchor_cache[p] = site_anchors.get(key, set())

    bad_target, bad_anchor, fixed = [], [], []
    for p in md_files:
        text = p.read_text(encoding="utf-8")
        changed = False
        for lineno, href in iter_links(p):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            target, _, frag = href.partition("#")
            if target:
                # 指向仓库内文件（可能在 docs 之外，如 ../../solutions/x.py）
                dest = (p.parent / target).resolve()
                # 题解页是 hooks/build_pages.py 在构建期生成的，磁盘上没有对应
                # 的 .md，得拿构建产物来判定存在与否。
                try:
                    rel_key = dest.relative_to(DOCS).as_posix()
                except ValueError:
                    rel_key = None
                # anchors_from_site() 把 solutions/index.html 记成 solutions.md
                keys = {rel_key, (rel_key or "").replace("/index.md", ".md")}
                if not dest.exists() and not (keys & set(site_anchors)):
                    bad_target.append((p, lineno, href))
                    continue
                if dest.suffix != ".md" or dest not in anchor_cache:
                    continue
            else:
                dest = p
            if not frag:
                continue
            have = anchor_cache[dest]
            if frag in have:
                continue
            # 尝试唯一匹配。差异几乎都出在连字符上（全角空格是否转成 `-`、
            # 编号里的 `.` 是否保留等），所以先把连字符全部抹掉再比。
            def norm_anchor(s):
                return s.replace("-", "")

            key = norm_anchor(frag)
            cands = [a for a in have if norm_anchor(a) == key]
            if not cands:                      # 退一步做包含匹配
                cands = [a for a in have
                         if key and (key in norm_anchor(a) or norm_anchor(a) in key)]
            if len(cands) == 1 and fix:
                text = text.replace("#" + frag + ")", "#" + cands[0] + ")")
                fixed.append((p, lineno, frag, cands[0]))
                changed = True
            else:
                bad_anchor.append((p, lineno, href, sorted(cands)[:3]))
        if changed:
            p.write_text(text, encoding="utf-8")

    L = ["# 链接校验报告\n",
         "> 由 `scripts/check_links.py` 生成。锚点规则与 `mkdocs.yml` 的 slugify 一致。\n",
         "**失效文件链接 {} 处　失效锚点 {} 处　自动修正 {} 处**\n".format(
             len(bad_target), len(bad_anchor), len(fixed))]
    if bad_target:
        L += ["## 指向不存在的文件\n", "| 文件 | 行 | 链接 |", "| --- | --- | --- |"]
        L += ["| {} | {} | `{}` |".format(p.relative_to(DOCS), n, h)
              for p, n, h in bad_target]
    if bad_anchor:
        L += ["\n## 锚点不存在\n", "| 文件 | 行 | 链接 | 相近候选 |", "| --- | --- | --- | --- |"]
        L += ["| {} | {} | `{}` | {} |".format(p.relative_to(DOCS), n, h,
                                               "、".join("`%s`" % c for c in c3) or "—")
              for p, n, h, c3 in bad_anchor]
    if fixed:
        L += ["\n## 已自动修正\n", "| 文件 | 行 | 原锚点 | 改为 |", "| --- | --- | --- | --- |"]
        L += ["| {} | {} | `{}` | `{}` |".format(p.relative_to(DOCS), n, a, b)
              for p, n, a, b in fixed]
    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")

    print("失效文件链接 {}，失效锚点 {}，自动修正 {}".format(
        len(bad_target), len(bad_anchor), len(fixed)))
    print("报告 -> {}".format(REPORT))
    return 1 if (bad_target or bad_anchor) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
