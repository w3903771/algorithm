"""MkDocs 构建钩子：把仓库里的东西变成站内可读的页面。

做三件事，全部在构建时完成，不往 docs/ 里落生成文件：

1. **题解站内阅读**：读 `solutions/*.py`，为 165 道题各生成一页
   （元信息 + 由文档字符串转成的解题思路 + 带行号的完整源码），
   再生成一张总览表 `solutions/index.md`。读者不用跳 GitHub 看源码。
2. **导航注入**：把 nav 里的 `solutions/index.md` 占位展开成
   「总览 + 笔试模板必刷 + 输入输出练习」三段，这样题解页也有上一页/下一页。
3. **章节盘**：首页与各部分索引页里的 `<!-- CHAPTER-MAP -->` 占位，
   在构建时按 nav 的真实结构渲染成章节网格——章节增删后索引不会过期。

题目元信息优先读 `docs/_problems.json`（由 scripts/gen_index.py 生成）；
拿不到就退回解析附录 A 的表格。两者都是入库文件，CI 上一定存在。

hooks 目录随仓库入库（scripts/ 被 .gitignore 排除，放不了构建期代码）。
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

try:  # MkDocs >= 1.5
    from mkdocs.structure.files import File
except ImportError:  # pragma: no cover
    File = None

ROOT = Path(__file__).resolve().parent.parent
SOLUTIONS = ROOT / "solutions"
DOCS = ROOT / "docs"

SETS = (
    ("BISHI", "笔试模板必刷", "BISHI1–147，牛客「笔试模板必刷」题单"),
    ("PIO", "输入输出练习", "PIO1–18，牛客「输入输出练习」题单"),
)

# 站内题解页的目录（相对 docs/）
OUT_DIR = "solutions"

_NUM = re.compile(r"^([A-Z]+)(\d+)$")
_SECTION = re.compile(r"^(\S[^\n]*?)[:：]\s*$")
_LIST_ITEM = re.compile(r"^(\d+[.、)]|[-*•])\s+")
_TAG_LIKE = re.compile(r"<(?=[A-Za-z/!])")
# 题解里常写 `docs/part3-数据结构/30-序列与数组.md`，站内直接连过去
_DOCS_PATH = re.compile(r"(?<![\[(])docs/(part\d+-[^/\s]+)/([^\s，。、）」`]+)\.md")


def _link_chapters(line: str) -> str:
    return _DOCS_PATH.sub(lambda m: f"[{m.group(2)}](../{m.group(1)}/{m.group(2)}.md)", line)


def sort_key(no: str):
    m = _NUM.match(no)
    return (m.group(1), int(m.group(2))) if m else (no, 0)


# --------------------------------------------------------------------------- #
# 元信息
# --------------------------------------------------------------------------- #

def _from_appendix() -> dict:
    """退路：从附录 A 的表格里解析题目元信息。"""
    p = DOCS / "appendix" / "A-牛客题单总索引.md"
    if not p.exists():
        return {}
    row = re.compile(
        r"^\|\s*\[((?:BISHI|PIO)\d+)\]\(([^)]+)\)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|"
        r"\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$"
    )
    out = {}
    for line in p.read_text(encoding="utf-8").split("\n"):
        m = row.match(line)
        if not m:
            continue
        no, url, title, diff, tags, chs, status = m.groups()
        out[no] = {
            "title": title,
            "url": url,
            "difficulty": diff,
            "tags": [] if tags in ("—", "") else tags.split("、"),
            "chapters": [] if chs in ("—", "") else chs.split("、"),
            "status": re.sub(r"\[|\]\([^)]*\)", "", status).strip(),
        }
    return out


def load_meta() -> dict:
    """题号 -> 元信息。_problems.json 优先，缺失字段用附录 A 补齐。"""
    meta = _from_appendix()
    p = DOCS / "_problems.json"
    if p.exists():
        try:
            for no, item in json.loads(p.read_text(encoding="utf-8")).items():
                meta.setdefault(no, {}).update(item)
        except (ValueError, OSError):
            pass

    # 章节归属：_mapping.json 是权威来源
    mp = DOCS / "_mapping.json"
    if mp.exists():
        try:
            data = json.loads(mp.read_text(encoding="utf-8"))["chapters"]
        except (ValueError, OSError, KeyError):
            data = {}
        for part, chapters in data.items():
            for chapter, problems in chapters.items():
                for no in problems:
                    meta.setdefault(no, {}).setdefault("refs", []).append((part, chapter))

    # 提交语言
    lang = SOLUTIONS / "_lang.json"
    if lang.exists():
        try:
            for no, name in json.loads(lang.read_text(encoding="utf-8")).items():
                if not no.startswith("_"):
                    meta.setdefault(no, {})["lang"] = name
        except (ValueError, OSError):
            pass

    for name, key in (("_verify_report.md", "verify"), ("_submit_report.md", "submit")):
        f = SOLUTIONS / name
        if not f.exists():
            continue
        row = re.compile(r"^\|\s*((?:BISHI|PIO)\d+)\s*\|\s*([^|]+?)\s*\|")
        for line in f.read_text(encoding="utf-8").split("\n"):
            m = row.match(line)
            if m:
                meta.setdefault(m.group(1), {})[key] = m.group(2)
    return meta


# --------------------------------------------------------------------------- #
# 文档字符串 -> Markdown
# --------------------------------------------------------------------------- #

def _escape(line: str) -> str:
    """转义会被当成 HTML 标签开头的 `<`，但保留行内代码里的原样。"""
    parts = line.split("`")
    for i in range(0, len(parts), 2):          # 偶数段在反引号之外
        parts[i] = _TAG_LIKE.sub("&lt;", parts[i])
    return "`".join(parts)


def _dedent(lines):
    pad = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
    return [l[pad:] if l.strip() else "" for l in lines]


def _render_body(lines) -> list:
    """一段章节正文：示意块转成代码块，列表与散文保持原样。

    判断标准是缩进：文档字符串里对照表、递推式、样例都靠缩进摆版，
    转成 Markdown 后必须落进代码块才不会被折行折散；
    而列表项的续行同样是缩进，所以要先认出列表、再看缩进。
    """
    out, buf, list_indent = [], [], None
    for line in _dedent(lines):
        stripped = line.strip()
        if not stripped:
            (buf if buf else out).append("")
            continue
        indent = len(line) - len(line.lstrip())
        was_list = list_indent is not None
        if _LIST_ITEM.match(stripped):
            if not was_list and out and out[-1]:
                out.append("")      # 列表要与上一段隔一个空行才会被解析成列表
            list_indent = indent
        elif list_indent is None or indent <= list_indent:
            list_indent = None
        if was_list and list_indent is None and out and out[-1]:
            out.append("")          # 列表后面紧跟散文，空行断开，别被当成续行
        # 缩进 >= 4 且不属于任何列表项 -> 原样保留的示意块
        if indent >= 4 and list_indent is None:
            buf.append(line)
            continue
        if buf:
            out += ["```text"] + _dedent(_strip_edges(buf)) + ["```", ""]
            buf = []
        out.append(_escape(_link_chapters(line)))
    if buf:
        out += ["```text"] + _dedent(_strip_edges(buf)) + ["```"]
    while out and not out[-1]:
        out.pop()
    return _promote_tables(out)


_ROW = re.compile(r"^\s*\|.*\|\s*$")


def _promote_tables(lines):
    """连着两行以上的 `| … | … |` 是表格，补一行分隔符让 Markdown 认得。

    文档字符串里的表格没写 `|---|`，不补的话会被当成普通段落，
    列就全糊在一起了。行首的 `|t| - |s|` 这类绝对值不会误伤：它们不成对出现，
    也不以 `|` 收尾。
    """
    out, i, fence = [], 0, False
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            fence = not fence
        if not fence and _ROW.match(line) and i + 1 < len(lines) and _ROW.match(lines[i + 1]):
            cols = len([c for c in line.strip().strip("|").split("|")])
            indent = line[:len(line) - len(line.lstrip())]
            out.append(line)
            out.append(indent + "|" + "|".join([" --- "] * cols) + "|")
            i += 1
            while i < len(lines) and _ROW.match(lines[i]):
                out.append(lines[i])
                i += 1
            continue
        out.append(line)
        i += 1
    return out


def _strip_edges(lines):
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def docstring_to_md(doc: str) -> tuple:
    """返回 (首段摘要, 正文 Markdown)。"""
    lines = doc.replace("\r\n", "\n").split("\n")
    lead, i = [], 0
    while i < len(lines) and lines[i].strip():
        lead.append(lines[i].strip())
        i += 1
    summary = " ".join(lead)

    body, section, buf = [], None, []

    def flush():
        if section:
            body.append(f"### {section}")
            body.append("")
        rendered = _render_body(buf) if buf else []
        if rendered:
            body.extend(rendered)
            body.append("")

    for line in lines[i:]:
        m = _SECTION.match(line)
        if m and not _LIST_ITEM.match(line):
            if section or buf:
                flush()
            section, buf = _escape(m.group(1).strip()), []
        else:
            buf.append(line)
    if section or [b for b in buf if b.strip()]:
        flush()
    return summary, "\n".join(body).strip()


# --------------------------------------------------------------------------- #
# 生成页面
# --------------------------------------------------------------------------- #

def _chips(no: str, m: dict) -> list:
    chips = []
    diff = m.get("difficulty")
    if diff and diff != "—":
        chips.append(f'<span class="chip chip--diff-{diff}">{diff}</span>')
    rate = m.get("acceptRate")
    if rate:
        chips.append(f'<span class="chip">通过率 {rate:g}%</span>')
    lang = m.get("lang", "python3")
    chips.append(f'<span class="chip chip--lang">{lang}</span>')
    if "PASS" in (m.get("verify") or ""):
        chips.append('<span class="chip chip--ok">样例通过</span>')
    if "通过" in (m.get("submit") or "") or "AC" in (m.get("submit") or ""):
        chips.append('<span class="chip chip--ok">牛客 AC</span>')
    for t in m.get("tags") or []:
        if t and t != "—":
            chips.append(f'<span class="chip chip--tag">{t}</span>')
    return chips


def _chapter_links(m: dict, chapter_index: dict) -> list:
    """章节归属 -> 站内链接。

    `_mapping.json` 的键是章节名，个别章名里的全角冒号在文件名里写成了连字符
    （118-分治进阶：整体二分与CDQ vs 118-分治进阶-整体二分与CDQ.md），
    所以一律按章号解析，不靠章名拼路径。
    """
    by_no = {}
    for path, title in chapter_index.items():
        num = re.match(r"^\d+", path.split("/")[-1])
        if num:
            by_no[num.group(0)] = (path, title)
    out = []
    for _, chapter in m.get("refs") or []:
        num = re.match(r"^\d+", chapter)
        hit = by_no.get(num.group(0)) if num else None
        out.append(f"[{hit[1]}](../{hit[0]})" if hit else chapter)
    if not out:
        out = list(m.get("chapters") or [])
    return out


def solution_page(no: str, m: dict, source: str, chapter_index: dict,
                  prev: str, nxt: str) -> str:
    tree = ast.parse(source)
    doc = ast.get_docstring(tree) or ""
    summary, body = docstring_to_md(doc)
    title = m.get("title") or no
    # 文档字符串首行通常是「BISHI1 标题 —— 一句话」，标题已经在 H1 里了
    summary = re.sub(rf"^{no}\s*(?:{re.escape(title)})?\s*(?:——|--|—)?\s*", "", summary)

    # 去掉文档字符串本身，正文里只留可运行的代码
    code = source
    if doc and tree.body and isinstance(tree.body[0], ast.Expr):
        end = getattr(tree.body[0], "end_lineno", None)
        if end:
            code = "\n".join(source.split("\n")[end:]).lstrip("\n")

    L = ["---", f"title: {no} {title}", "---", "",
         f"# {no}　{title}", "",
         '<div class="chips">' + "".join(_chips(no, m)) + "</div>", ""]

    links = []
    if m.get("url"):
        links.append(f'[牛客原题 :octicons-link-external-16:]({m["url"]}){{ target="_blank" }}')
    links.append(
        f'[源码 :octicons-mark-github-16:](https://github.com/w3903771/algorithm/'
        f'blob/main/solutions/{no}.py){{ target="_blank" }}'
    )
    chapters = _chapter_links(m, chapter_index)
    L.append("　".join(links))
    if chapters:
        L += ["", "**讲解章节**：" + "、".join(chapters)]
    L.append("")

    if summary:
        L += ["!!! abstract \"一句话\"", "", "    " + summary.replace("\n", "\n    "), ""]
    if body:
        L += ["## 解题思路", "", body, ""]
    L += ["## 参考实现", "",
          f'```python title="solutions/{no}.py" linenums="1"', code.rstrip(), "```", ""]

    nav = []
    if prev:
        nav.append(f"[:octicons-arrow-left-16: {prev}]({prev}.md)")
    if nxt:
        nav.append(f"[{nxt} :octicons-arrow-right-16:]({nxt}.md)")
    if nav:
        L += ['<div class="pager">' + "　".join(nav) + "</div>", ""]
    return "\n".join(L)


def index_page(groups: dict, meta: dict) -> str:
    total = sum(len(v) for v in groups.values())
    passed = sum(1 for no in meta if "PASS" in (meta[no].get("verify") or ""))
    L = ["---", "title: 题解", "---", "",
         "# 题解", "",
         f"牛客 **{total} 题**的 Python 题解，全部在站内直接阅读："
         "每页都是「元信息 → 解题思路 → 完整源码」，思路来自题解文件本身的文档字符串。", "",
         f'<div class="chips"><span class="chip chip--ok">{passed} / {total} 通过官方样例</span>'
         '<span class="chip chip--ok">165 / 165 通过牛客判题机</span>'
         '<span class="chip">5 题登记为 PyPy3</span></div>', ""]
    for prefix, name, desc in SETS:
        items = groups.get(prefix) or []
        if not items:
            continue
        L += [f"## {name}", "", desc + f"，共 {len(items)} 题。", "",
              '<div class="q-table" markdown>', "",
              "| 题号 | 标题 | 难度 | 讲解章节 | 状态 |",
              "| --- | --- | --- | --- | --- |"]
        for no in items:
            m = meta.get(no, {})
            chs = "、".join(m.get("chapters") or []) or "—"
            ok = "✅" if "PASS" in (m.get("verify") or "") else "—"
            lang = m.get("lang")
            if lang and lang != "python3":
                ok += f" {lang}"
            L.append(f"| [{no}]({no}.md) | {m.get('title', '')} | "
                     f"{m.get('difficulty', '—')} | {chs} | {ok} |")
        L += ["", "</div>", ""]
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# 章节盘
# --------------------------------------------------------------------------- #

def _walk_nav(items, parts=None):
    """从 nav 配置里抽出 [(部分标题, [(章号, 标题, 路径)])]。"""
    parts = [] if parts is None else parts
    for item in items or []:
        if not isinstance(item, dict):
            continue
        for title, value in item.items():
            if not isinstance(value, list):
                continue
            chapters = []
            for child in value:
                if isinstance(child, str):          # navigation.indexes 的索引页
                    continue
                if not isinstance(child, dict):
                    continue
                for label, path in child.items():
                    if isinstance(path, str) and path.endswith(".md"):
                        chapters.append((label, path))
            # 只收正文部分（partN-*），附录 / 题解不进章节盘
            if chapters and chapters[0][1].startswith("part"):
                parts.append((title, chapters))
    return parts


def _split_label(label: str):
    m = re.match(r"^\s*(\d+)\s*·\s*(.+)$", label)
    return (m.group(1), m.group(2)) if m else ("", label)


def chapter_map(parts, counts: dict, base: str, only: str = None) -> str:
    cls = "chapter-map chapter-map--single" if only else "chapter-map"
    html = [f'<div class="{cls}">']
    for part, chapters in parts:
        if only and part != only:
            continue
        if not only:
            first = chapters[0][1].split("/")[0]
            html.append(f'<section class="cm-part">'
                        f'<h3 class="cm-part__title">'
                        f'<a href="{base}{first}/">{part}</a>'
                        f'<span class="cm-part__count">{len(chapters)} 章</span></h3>'
                        f'<ol class="cm-list">')
        else:
            html.append('<section class="cm-part"><ol class="cm-list">')
        for label, path in chapters:
            num, title = _split_label(label)
            href = base + path[:-3].replace("/index", "") + "/"
            n = counts.get(path, 0)
            ex = f'<span class="cm-item__ex">{n} 题</span>' if n else ""
            html.append(f'<li class="cm-item"><a href="{href}">'
                        f'<span class="cm-item__no">{num}</span>'
                        f'<span class="cm-item__title">{title}</span>{ex}</a></li>')
        html.append("</ol></section>")
    html.append("</div>")
    return "\n".join(html)


# --------------------------------------------------------------------------- #
# MkDocs 事件
# --------------------------------------------------------------------------- #

_state = {}


def on_config(config):
    meta = load_meta()
    groups = {}
    for p in SOLUTIONS.glob("*.py"):
        if p.stem.startswith("_"):
            continue
        prefix = _NUM.match(p.stem)
        groups.setdefault(prefix.group(1) if prefix else "OTHER", []).append(p.stem)
    for key in groups:
        groups[key].sort(key=sort_key)

    _state["meta"] = meta
    _state["groups"] = groups

    # 例题数：章节路径 -> 题目数
    counts = {}
    mp = DOCS / "_mapping.json"
    if mp.exists():
        try:
            data = json.loads(mp.read_text(encoding="utf-8"))["chapters"]
            for part, chapters in data.items():
                for chapter, problems in chapters.items():
                    counts[f"{part}/{chapter}.md"] = len(problems)
        except (ValueError, OSError, KeyError):
            pass
    _state["counts"] = counts
    _state["parts"] = _walk_nav(config.get("nav"))
    _state["chapter_index"] = {
        path: _split_label(label)[1]
        for _, chapters in _state["parts"] for label, path in chapters
    }

    # nav 占位 -> 题解三段
    def expand(items):
        out = []
        for item in items or []:
            if isinstance(item, dict):
                new = {}
                for title, value in item.items():
                    if value == f"{OUT_DIR}/index.md":
                        new[title] = [f"{OUT_DIR}/index.md"] + [
                            {name: [{no: f"{OUT_DIR}/{no}.md"} for no in groups.get(prefix, [])]}
                            for prefix, name, _ in SETS if groups.get(prefix)
                        ]
                    elif isinstance(value, list):
                        new[title] = expand(value)
                    else:
                        new[title] = value
                out.append(new)
            else:
                out.append(item)
        return out

    if config.get("nav"):
        config["nav"] = expand(config["nav"])
    return config


def on_files(files, config):
    if File is None:
        return files
    meta, groups = _state["meta"], _state["groups"]
    ordered = [no for prefix, _, _ in SETS for no in groups.get(prefix, [])]
    pos = {no: i for i, no in enumerate(ordered)}

    for no in ordered:
        src = (SOLUTIONS / f"{no}.py").read_text(encoding="utf-8")
        i = pos[no]
        content = solution_page(
            no, meta.get(no, {}), src, _state["chapter_index"],
            ordered[i - 1] if i else "", ordered[i + 1] if i + 1 < len(ordered) else "",
        )
        files.append(File.generated(config, f"{OUT_DIR}/{no}.md", content=content))
    files.append(File.generated(config, f"{OUT_DIR}/index.md",
                                content=index_page(groups, meta)))
    return files


def on_page_markdown(markdown, page, config, files):
    if "<!-- CHAPTER-MAP" not in markdown:
        return markdown
    src = page.file.src_uri
    depth = src.count("/")
    base = "../" * depth if depth else ""

    # 部分索引页只渲染自己那一部分，首页渲染全书
    folder = src.split("/")[0] if depth else ""
    only = next((title for title, chapters in _state["parts"]
                 if chapters[0][1].startswith(folder + "/")), None) if folder else None

    def repl(m):
        return chapter_map(_state["parts"], _state["counts"], base, only)

    return re.sub(r"<!-- CHAPTER-MAP(?::[^>]*)? -->", repl, markdown)
