"""抓取菜鸟教程 Python3 全部章节 -> sources/04-runoob/

入口: https://www.runoob.com/python3/python3-list.html 的左侧目录（覆盖 Python3 教程全部页面）
用法: uv run python scripts/runoob_fetch.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup, NavigableString, Tag

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nc_common import get  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "sources" / "04-runoob"
OUT.mkdir(parents=True, exist_ok=True)

ENTRY = "https://www.runoob.com/python3/python3-list.html"


# ---------------------------------------------------------------- 目录

def collect_links() -> list:
    html = get(ENTRY)
    soup = BeautifulSoup(html, "lxml")
    side = soup.select_one("#leftcolumn")
    seen, items = set(), []
    for a in side.find_all("a"):
        href = a.get("href") or ""
        if not href or href.startswith("#"):
            continue
        url = urljoin(ENTRY, href)
        if "runoob.com" not in url:
            continue
        title = " ".join(a.get_text(" ", strip=True).split())
        if url in seen or not title:
            continue
        seen.add(url)
        items.append({"title": title, "url": url})
    return items


# ---------------------------------------------------------------- 正文转换

def code_text(node: Tag) -> str:
    """从 runoob 的高亮代码块里还原纯文本。"""
    out = []

    def walk(n):
        if isinstance(n, NavigableString):
            out.append(str(n))
            return
        if not isinstance(n, Tag):
            return
        if n.name == "br":
            out.append("\n")
            return
        for c in n.children:
            walk(c)

    walk(node)
    txt = "".join(out).replace(" ", " ").replace("\r", "")
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    # runoob 代码块每行既有 <br> 又有源码换行，整体呈双倍行距。
    # 若文中不存在任何孤立的 \n（换行全部成对），就折半还原。
    if "\n\n" in txt and re.search(r"(?<!\n)\n(?!\n)", txt) is None:
        txt = txt.replace("\n\n", "\n")
    return txt.strip("\n")


def guess_lang(code: str) -> str:
    if re.search(r"^\s*(def |class |import |from |print\(|#!/usr/bin/(env )?python)", code, re.M):
        return "python"
    if re.search(r"^\s*(\$|>>>)", code, re.M):
        return "shell" if code.lstrip().startswith("$") else "python"
    return "python"


def to_md(node: Tag, base_url: str) -> str:
    parts = []

    def inline(n) -> str:
        if isinstance(n, NavigableString):
            return str(n).replace(" ", " ")
        if not isinstance(n, Tag):
            return ""
        name = n.name.lower()
        if name == "br":
            return "\n"
        if name in ("b", "strong"):
            s = "".join(inline(c) for c in n.children).strip()
            return f"**{s}**" if s else ""
        if name in ("i", "em"):
            s = "".join(inline(c) for c in n.children).strip()
            return f"*{s}*" if s else ""
        if name == "code":
            s = "".join(inline(c) for c in n.children).strip()
            return f"`{s}`" if s else ""
        if name == "a":
            s = "".join(inline(c) for c in n.children).strip()
            href = urljoin(base_url, n.get("href") or "")
            return f"[{s}]({href})" if s and href else s
        if name == "img":
            src = urljoin(base_url, n.get("src") or "")
            return f"\n\n![{n.get('alt','')}]({src})\n\n"
        return "".join(inline(c) for c in n.children)

    def table_md(t: Tag) -> str:
        rows = []
        for tr in t.find_all("tr"):
            cells = [" ".join(inline(td).split()).replace("|", "\\|")
                     for td in tr.find_all(["td", "th"])]
            if cells:
                rows.append(cells)
        if not rows:
            return ""
        n = max(len(r) for r in rows)
        rows = [r + [""] * (n - len(r)) for r in rows]
        out = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join(["---"] * n) + " |"]
        out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
        return "\n".join(out)

    def block(n):
        if isinstance(n, NavigableString):
            s = str(n).strip()
            if s:
                parts.append(s)
            return
        if not isinstance(n, Tag):
            return
        name = n.name.lower()
        cls = " ".join(n.get("class") or [])

        if name in ("script", "style", "ins", "iframe", "noscript"):
            return
        if "ad" in cls.split() or cls.startswith("adsbygoogle"):
            return

        if name == "div" and "example" in cls.split():
            # 实例块：标题 + 代码 + 可能的结果
            h = n.find(["h2", "h3"])
            if h:
                parts.append(f"**{h.get_text(' ', strip=True)}**\n")
            ec = n.select_one(".example_code")
            if ec:
                code = code_text(ec)
                parts.append(f"```{guess_lang(code)}\n{code}\n```")
            for pre in n.find_all("pre", recursive=True):
                if ec and pre in ec.descendants:
                    continue
                parts.append("```\n" + code_text(pre) + "\n```")
            return
        if name == "pre":
            parts.append("```\n" + code_text(n) + "\n```")
            return
        if name == "table":
            md = table_md(n)
            if md:
                parts.append(md)
            return
        if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            lvl = int(name[1])
            parts.append("#" * min(lvl + 1, 6) + " " + n.get_text(" ", strip=True))
            return
        if name in ("ul", "ol"):
            ordered = name == "ol"
            for i, li in enumerate(n.find_all("li", recursive=False), 1):
                s = " ".join(inline(li).split())
                if s:
                    parts.append(f"{i}. {s}" if ordered else f"- {s}")
            return
        if name in ("p", "blockquote", "div", "section"):
            # 含块级子元素则递归，否则整体成段
            if n.find(["div", "table", "pre", "ul", "ol", "h1", "h2", "h3", "h4"], recursive=False):
                for c in n.children:
                    block(c)
            else:
                s = inline(n).strip()
                if s:
                    parts.append(("> " + s) if name == "blockquote" else s)
            return
        if name == "hr":
            parts.append("---")
            return
        s = inline(n).strip()
        if s:
            parts.append(s)

    for c in node.children:
        block(c)

    text = "\n\n".join(p for p in parts if p and p.strip())
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------- 主流程

def slugify(url: str) -> str:
    name = url.rstrip("/").split("/")[-1]
    return re.sub(r"\.html?$", "", name) or "index"


def main() -> int:
    links = collect_links()
    print(f"目录共 {len(links)} 个页面")
    (OUT / "_links.json").write_text(json.dumps(links, ensure_ascii=False, indent=2), encoding="utf-8")

    index = []
    for i, it in enumerate(links, 1):
        slug = slugify(it["url"])
        dst = OUT / f"{i:02d}-{slug}.md"
        if dst.exists() and dst.stat().st_size > 200:
            index.append((it["title"], dst.name, dst.stat().st_size))
            continue
        html = get(it["url"])
        if not html:
            print(f"  [fail] {it['title']} {it['url']}")
            continue
        soup = BeautifulSoup(html, "lxml")
        art = soup.select_one(".article-intro") or soup.select_one("#content")
        if art is None:
            print(f"  [nocontent] {it['title']}")
            continue
        body = to_md(art, it["url"])
        dst.write_text(
            f"# {it['title']}\n\n> 来源: {it['url']}\n\n---\n\n{body}\n", encoding="utf-8")
        index.append((it["title"], dst.name, len(body)))
        print(f"  [{i}/{len(links)}] {it['title']} -> {dst.name} ({len(body)} 字符)")

    lines = ["# 菜鸟教程 Python3 抓取索引\n",
             f"> 入口: {ENTRY}　共 {len(index)} 页\n",
             "| # | 章节 | 文件 | 字符数 |", "| --- | --- | --- | --- |"]
    for n, (title, fname, size) in enumerate(index, 1):
        lines.append(f"| {n} | {title} | [{fname}]({fname}) | {size} |")
    (OUT / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n完成 {len(index)} 页 -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
