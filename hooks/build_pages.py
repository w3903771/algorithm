"""MkDocs 构建钩子：把仓库里的东西变成站内可读的页面。

做三件事，全部在构建时完成，不往 docs/ 里落生成文件：

1. **题解站内阅读**：读 `solutions/<site>/<题号>/sol.py`，为每道题各生成一页
   （元信息 + 由文档字符串转成的解题思路 + 带行号的完整源码），
   再生成一张总览表 `solutions/index.md`。读者不用跳 GitHub 看源码。
2. **导航注入**：把 nav 里的 `solutions/index.md` 占位展开成
   「总览 + 各来源 / 各题单」的两级结构，这样题解页也有上一页/下一页。
3. **章节盘**：首页与各部分索引页里的 `<!-- CHAPTER-MAP -->` 占位，
   在构建时按 nav 的真实结构渲染成章节网格——章节增删后索引不会过期。

题目元信息优先读 `data/_problems.json`（由 scripts/gen_index.py 生成）；
拿不到就退回解析附录 A 的表格。两者都是入库文件，CI 上一定存在。

题单分组读 `data/_sources.json`——新增一套题单只改那份注册表，这里不用动。
`solutions/` 自 P-M③ 起**按站点分层、一题一目录**（02 号文件 §6.1），
但**站内 URL 与物理布局解耦**：`on_files` 自己拼站内页路径，站内页始终是
`solutions/<题号>.md`，正文里的 `[题号](../solutions/题号.md)` 引用
既不会因为加题单失效，也没有随 P-M③ 改过一处。
题号 -> 目录的查表统一走 `scripts/sol_store.py`，本文件不自己拼路径。

章节路径自 P-M① 起是 **id**（`ds/array`、`math/number/basic`），不带章号也不带中文。
章号只活在 nav 的标签里，`_split_label` 负责把它和标题拆开——
所以本文件里任何「按章号解析路径」的老写法都已删掉，一律按 id 查表。
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

try:  # MkDocs >= 1.5
    from mkdocs.structure.files import File
except ImportError:  # pragma: no cover
    File = None

ROOT = Path(__file__).resolve().parent.parent
# 题号 -> 目录的查表只有一份实现，放在 scripts/ 下由 9 个消费方共用（08 号文件 §6.1）。
# CI 是完整 checkout，scripts/ 自 P0a 起已入库，构建期 import 得到。
# 追加而不是插到最前：这是构建期进程，前插会让 scripts/ 里的模块名盖住
# mkdocs 及其插件要 import 的同名模块。今天 37 个模块名与已装包零碰撞，
# 但那是巧合，不是保证。
sys.path.append(str(ROOT / "scripts"))
import sol_store as store  # noqa: E402

SOLUTIONS = ROOT / "solutions"
DOCS = ROOT / "docs"
# 公开数据在根 data/（P-S① 从 dev/data/ 搬出：dev/ 私有化后构建期仍要读它）。hook 用 ROOT 定位，
# 本来就在读 docs/ 之外的 solutions/，访问 dev/ 无障碍；CI 是完整 checkout 后构建。
DATA = ROOT / "data"

_FALLBACK_SETS = (
    ("BISHI", "牛客", "笔试模板必刷", "BISHI1–147，牛客「笔试模板必刷」题单"),
    ("PIO", "牛客", "输入输出练习", "PIO1–18，牛客「输入输出练习」题单"),
)


def load_sets() -> tuple:
    """题单注册表 -> (前缀, 来源名, 题单名, 说明) 列表，顺序即导航顺序。

    hooks 在构建期跑，任何异常都会让整站构建失败，所以这里读坏了就退回硬编码，
    最差也只是新题单不分组，站还是能出。
    """
    p = DATA / "_sources.json"
    if not p.exists():
        return _FALLBACK_SETS
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        sites = d["sites"]
        out = []
        for s in d["sets"]:
            site = sites.get(s["site"], {})
            out.append((s["prefix"], site.get("name", s["site"]), s["name"],
                        s.get("desc") or f"{s.get('range', '')}，{site.get('name', '')}「{s['name']}」题单"))
        return tuple(out) or _FALLBACK_SETS
    except (ValueError, OSError, KeyError):
        return _FALLBACK_SETS


SETS = ()   # on_config 里填充；模块级留空是为了让 load_sets 能用到 DOCS

# 站内题解页的目录（相对 docs/）
OUT_DIR = "solutions"

_NUM = re.compile(r"^([A-Z]+)(\d+)$")
_SECTION = re.compile(r"^(\S[^\n]*?)[:：]\s*$")
_LIST_ITEM = re.compile(r"^(\d+[.、)]|[-*•])\s+")
_TAG_LIKE = re.compile(r"<(?=[A-Za-z/!])")
# 题解里常写 `docs/ds/array.md`，站内直接连过去。id 是全小写连字符的多段路径，
# 段数不定（`ds/array` 两段、`math/number/basic` 三段）。
_DOCS_PATH = re.compile(r"(?<![\[(])docs/([a-z0-9][a-z0-9-]*(?:/[a-z0-9][a-z0-9-]*)+)\.md")


def _link_chapters(line: str) -> str:
    """裸写的章路径 -> 站内链接，链接文字用该章的中文标题。

    题解页在 `solutions/<题号>.md`，相对 docs/ 只有一层，
    所以 `../<id>.md` 对任意深度的 id 都成立。
    查不到标题就原样留着——宁可显示成路径，也不要编一个不存在的章名。
    """
    index = _state.get("chapter_index") or {}

    def repl(m):
        page = m.group(1) + ".md"
        title = index.get(page)
        return f"[{title}](../{page})" if title else m.group(0)

    return _DOCS_PATH.sub(repl, line)


def sort_key(no: str):
    m = _NUM.match(no)
    return (m.group(1), int(m.group(2))) if m else (no, 0)


# --------------------------------------------------------------------------- #
# 元信息
# --------------------------------------------------------------------------- #

def _from_appendix() -> dict:
    """退路：从附录 A 的表格里解析题目元信息。"""
    p = DOCS / "appendix" / "a-problems.md"
    for legacy in ("A-题单总索引.md", "A-牛客题单总索引.md"):   # P-M① 改名前的旧文件名
        if p.exists():
            break
        p = DOCS / "appendix" / legacy
    if not p.exists():
        return {}
    # 题号前缀不写死：新题单（BM / LC / …）的行也要能被这条退路解析到
    row = re.compile(
        r"^\|\s*\[([A-Z]+\d+)\]\(([^)]+)\)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|"
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
    p = DATA / "_problems.json"
    if p.exists():
        try:
            for no, item in json.loads(p.read_text(encoding="utf-8")).items():
                meta.setdefault(no, {}).update(item)
        except (ValueError, OSError):
            pass

    # 章节归属：_mapping.json 是权威来源
    mp = DATA / "_mapping.json"
    if mp.exists():
        try:
            data = json.loads(mp.read_text(encoding="utf-8"))["chapters"]
        except (ValueError, OSError, KeyError):
            data = {}
        for page_id, problems in data.items():
            for no in problems:
                meta.setdefault(no, {}).setdefault("refs", []).append(page_id)

    # 提交语言：原 solutions/_lang.json，P-M③ 起并进各题的 meta.json
    for no, name in store.submit_langs().items():
        meta.setdefault(no, {})["lang"] = name

    for name, key in (("_verify_report.md", "verify"), ("_submit_report.md", "submit")):
        f = SOLUTIONS / name
        if not f.exists():
            continue
        row = re.compile(r"^\|\s*([A-Z]+\d+)\s*\|\s*([^|]+?)\s*\|")
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
    if m.get("mode") == "core":
        chips.append('<span class="chip">核心代码模式</span>')
    if m.get("group"):
        chips.append(f'<span class="chip chip--tag">{m["group"]}</span>')
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

    `_mapping.json` 自 P-M① 起直接以新 id 为键，加个 `.md` 就是 nav 里的路径，
    不再需要「按章号反查」那套绕路——旧写法是为了绕开章名里的全角冒号
    与文件名不一致（118-分治进阶：整体二分与CDQ vs …-整体二分与CDQ.md），
    新 id 里没有这个问题。**顺序按本表原样**，那就是章号顺序。
    """
    out = []
    for page_id in m.get("refs") or []:
        page = f"{page_id}.md"
        title = chapter_index.get(page)
        out.append(f"[{title}](../{page})" if title else page_id)
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
        f'blob/main/{store.sol_path(no).relative_to(ROOT).as_posix()})'
        f'{{ target="_blank" }}'
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
          f'```python title="{store.sol_path(no).relative_to(ROOT).as_posix()}" '
          f'linenums="1"', code.rstrip(), "```", ""]

    nav = []
    if prev:
        nav.append(f"[:octicons-arrow-left-16: {prev}]({prev}.md)")
    if nxt:
        nav.append(f"[{nxt} :octicons-arrow-right-16:]({nxt}.md)")
    if nav:
        L += ['<div class="pager">' + "　".join(nav) + "</div>", ""]
    return "\n".join(L)


def _site_names() -> dict:
    """`{站点短名: 中文站名}`，读 `data/_sources.json`。接洛谷时只改那一份。"""
    try:
        d = json.loads((DATA / "_sources.json").read_text(encoding="utf-8"))
        return {k: v.get("name", k) for k, v in (d.get("sites") or {}).items()}
    except (ValueError, OSError, AttributeError):
        return {}


_SITE_NAMES = _site_names()


def index_page(groups: dict, meta: dict) -> str:
    total = sum(len(v) for v in groups.values())
    passed = sum(1 for no in meta if "PASS" in (meta[no].get("verify") or ""))
    judged = sum(1 for no in meta
                 if any(k in (meta[no].get("submit") or "") for k in ("通过", "AC")))
    pypy = sum(1 for no in meta if (meta[no].get("lang") or "python3") != "python3")

    # 判题机是**分站点**的：原先一律写「牛客判题机」，而 P-M③ 之后有 100 道力扣题
    # 也在这个计数里（P1③ 锁定复核实测）。站名从注册表取，接洛谷时这里不用再改。
    by_site = {}
    for no in meta:
        if any(k in (meta[no].get("submit") or "") for k in ("通过", "AC")):
            nm = _SITE_NAMES.get(meta[no].get("site") or "", meta[no].get("site") or "")
            by_site[nm] = by_site.get(nm, 0) + 1

    chips = [f'<span class="chip chip--ok">{passed} / {total} 通过官方样例</span>']
    if judged:
        detail = "＋".join(f"{nm} {n}" for nm, n in sorted(by_site.items(), key=lambda x: -x[1]) if nm)
        label = f"{judged} 题通过判题机" + (f"（{detail}）" if len(by_site) > 1 else "")
        chips.append(f'<span class="chip chip--ok">{label}</span>')
    if pypy:
        chips.append(f'<span class="chip">{pypy} 题登记为 PyPy3</span>')

    L = ["---", "title: 题解", "---", "",
         "# 题解", "",
         f"**{total} 题**的 Python 题解，全部在站内直接阅读："
         "每页都是「元信息 → 解题思路 → 完整源码」，思路来自题解文件本身的文档字符串。", "",
         '<div class="chips">' + "".join(chips) + "</div>", ""]

    last_site = None
    for prefix, site, name, desc in SETS:
        items = groups.get(prefix) or []
        if not items:
            continue
        if site != last_site:
            L += [f"## {site}", ""]
            last_site = site
        # 力扣题单自带官方专题分组，多一列比塞进标签里好读
        has_group = any(meta.get(no, {}).get("group") for no in items)
        L += [f"### {name}", "", desc + f"　共 {len(items)} 题。", "",
              '<div class="q-table" markdown>', "",
              "| 题号 | 标题 |" + (" 专题 |" if has_group else "") + " 难度 | 讲解章节 | 状态 |",
              "| --- | --- |" + (" --- |" if has_group else "") + " --- | --- | --- |"]
        for no in items:
            m = meta.get(no, {})
            chs = "、".join(m.get("chapters") or []) or "—"
            ok = "✅" if "PASS" in (m.get("verify") or "") else "—"
            lang = m.get("lang")
            if lang and lang != "python3":
                ok += f" {lang}"
            grp = f" {m.get('group', '—')} |" if has_group else ""
            L.append(f"| [{no}]({no}.md) | {m.get('title', '')} |{grp} "
                     f"{m.get('difficulty', '—')} | {chs} | {ok} |")
        L += ["", "</div>", ""]
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# 章节盘
# --------------------------------------------------------------------------- #

# 章节盘不收的顶层目录：附录与题解各有自己的索引
_NOT_CHAPTERS = ("appendix", "solutions")


def _iter_nav(items, section=None):
    """递归产出 (所在 nav 分组标题, 标签, 路径)。nav 现在是三层：卷 → 目录 → 章。"""
    for item in items or []:
        if not isinstance(item, dict):
            continue                                # navigation.indexes 的目录页，裸字符串
        for title, value in item.items():
            if isinstance(value, list):
                for row in _iter_nav(value, title):
                    yield row
            elif isinstance(value, str) and value.endswith(".md"):
                yield section, title, value


def _walk_nav(items):
    """从 nav 配置里抽出 [(目录, 目录标题, [(标签, 路径)])]。

    **按目录归组，不按卷归组**：nav 顶层是三卷，但同一个目录会横跨两卷
    （`ds/stack` 卷一、`ds/balanced-tree` 卷三）。章节盘要么按目录成块，
    要么把 `ds/` 切成两半——后者会让 `ds/index.md` 认不出自己那一份。
    目录标题取该目录**第一次出现**时所在的 nav 分组名。
    """
    order, groups, titles = [], {}, {}
    for section, label, path in _iter_nav(items):
        if "/" not in path or path.endswith("/index.md"):
            continue                                # 首页与各目录索引页
        folder = path.split("/")[0]
        if folder in _NOT_CHAPTERS:
            continue
        if folder not in groups:
            groups[folder], titles[folder] = [], section or folder
            order.append(folder)
        groups[folder].append((label, path))
    return [(f, titles[f], groups[f]) for f in order]


def _walk_volumes(items) -> list:
    """nav **顶层**分组各有多少章，按 nav 顺序回 `[(标题, 章数), …]`。

    `_walk_nav()` 是按**目录**归组的（一个目录会横跨两卷），这里要的正好相反——
    按**卷**归组，因为首页要说「卷一多少章、卷二多少章」。
    两个函数走的是同一棵 nav，只是在不同层上收口。

    不收「首页 / 题解 / 附录」：它们是顶层条目或非章内容。
    """
    out = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        for title, value in item.items():
            if not isinstance(value, list):
                continue                        # 首页那种 `标题: 路径.md`
            n = sum(1 for _, _, path in _iter_nav(value)
                    if "/" in path and not path.endswith("/index.md")
                    and path.split("/")[0] not in _NOT_CHAPTERS)
            if n:
                out.append((title, n))
    return out


def _split_label(label: str):
    # 章号允许字母后缀：拆章产生的新章用「源章号 + 字母」（39A / 39B / 39C），
    # 这样不必重排现有章号——正文里带章号的引用还没清洗（那是 P1 的活）。
    m = re.match(r"^\s*(\d+[A-Z]?)\s*·\s*(.+)$", label)
    return (m.group(1), m.group(2)) if m else ("", label)


def _folder_href(folder: str, chapters: list, base: str) -> str:
    """目录标题指向该目录的索引页；还没有索引页的目录（geometry / technique）
    退而指向它的第一章，免得点出个 404。索引页是 P6 的活。"""
    if (DOCS / folder / "index.md").exists():
        return f"{base}{folder}/"
    return base + chapters[0][1][:-3] + "/"


def chapter_map(parts, counts: dict, base: str, only: str = None) -> str:
    cls = "chapter-map chapter-map--single" if only else "chapter-map"
    html = [f'<div class="{cls}">']
    for folder, part, chapters in parts:
        if only and folder != only:
            continue
        if not only:
            html.append(f'<section class="cm-part">'
                        f'<h3 class="cm-part__title">'
                        f'<a href="{_folder_href(folder, chapters, base)}">{part}</a>'
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


def _solution_nav(groups: dict) -> list:
    """题解导航：来源 -> 题单 -> 各题，两级分组。

    同一来源下的多套题单收在一个折叠项里，否则四套题单平铺会把侧栏顶满；
    只有一套题单的来源也照样加这一层，结构统一，读者不用猜。
    """
    out, by_site = [], {}
    for prefix, site, name, _ in SETS:
        items = groups.get(prefix) or []
        if items:
            by_site.setdefault(site, []).append(
                {name: [{no: f"{OUT_DIR}/{no}.md"} for no in items]})
    for site, sets_ in by_site.items():
        out.append({site: sets_})
    return out


def on_config(config):
    global SETS
    SETS = load_sets()
    meta = load_meta()
    groups = {}
    for no in store.all_numbers():
        prefix = _NUM.match(no)
        groups.setdefault(prefix.group(1) if prefix else "OTHER", []).append(no)
    for key in groups:
        groups[key].sort(key=sort_key)

    _state["meta"] = meta
    _state["groups"] = groups

    # 例题数：章节路径 -> 题目数
    counts, chapter_problems = {}, {}
    mp = DATA / "_mapping.json"
    if mp.exists():
        try:
            data = json.loads(mp.read_text(encoding="utf-8"))["chapters"]
            for page_id, problems in data.items():
                counts[f"{page_id}.md"] = len(problems)
                chapter_problems[page_id] = list(problems)
        except (ValueError, OSError, KeyError):
            pass
    _state["counts"] = counts
    _state["chapter_problems"] = chapter_problems
    _state["parts"] = _walk_nav(config.get("nav"))
    _state["volumes"] = _walk_volumes(config.get("nav"))
    _state["chapter_index"] = {
        path: _split_label(label)[1]
        for _, _, chapters in _state["parts"] for label, path in chapters
    }

    # nav 占位 -> 题解三段
    def expand(items):
        out = []
        for item in items or []:
            if isinstance(item, dict):
                new = {}
                for title, value in item.items():
                    if value == f"{OUT_DIR}/index.md":
                        new[title] = [f"{OUT_DIR}/index.md"] + _solution_nav(groups)
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
    ordered = [no for prefix, _, _, _ in SETS for no in groups.get(prefix, [])]
    pos = {no: i for i, no in enumerate(ordered)}

    for no in ordered:
        src = store.sol_path(no).read_text(encoding="utf-8")
        i = pos[no]
        content = solution_page(
            no, meta.get(no, {}), src, _state["chapter_index"],
            ordered[i - 1] if i else "", ordered[i + 1] if i + 1 < len(ordered) else "",
        )
        files.append(File.generated(config, f"{OUT_DIR}/{no}.md", content=content))
    files.append(File.generated(config, f"{OUT_DIR}/index.md",
                                content=index_page(groups, meta)))
    return files


# --------------------------------------------------------------------------- #
# 题号引用的渲染层展开（04 号文件 §四）
# --------------------------------------------------------------------------- #

# 只认「链接文字整段就是一个题号」这一种形状：`[BISHI136](../solutions/BISHI136.md)`。
# 正文源码一个字不改，展开只发生在渲染层。
_PROB_LINK = re.compile(r"\[((?:BISHI|PIO|BM|LC)\d+|P\d{3,})\]\(([^)\s]+)\)")
_FENCE_LINE = re.compile(r"^\s*(```|~~~)")


def _expand_one(no: str, title: str, site: str) -> tuple:
    """`(链接文字, title 属性)`——**展开规则分平台**（04 §四 的 v2 修正）。

    | 题源 | 读者认不认得题号 | 展开为 |
    | --- | --- | --- |
    | 洛谷 `P3372` | 认得，是社区通用标识 | `P3372 【模板】线段树 1` |
    | 力扣 `LC1`   | 认得，题号广泛使用   | `LC 1. 两数之和` |
    | 牛客 `BISHI136` | **不认得**，本项目自造 | `【模板】01背包`，题号退进 `title` |

    一刀切地全部隐藏题号会损失洛谷 / 力扣读者的检索能力。
    """
    if no.startswith("P") and no[1:].isdigit():          # 洛谷
        return f"{no} {title}", ""
    if no.startswith("LC"):                              # 力扣
        return f"LC {no[2:]}. {title}", ""
    return title, no                                     # 牛客题单：题号隐入 title


def _expand_problem_refs(markdown: str) -> str:
    """把正文行内的题号引用展开成题名。查不到题名就原样留着。

    **三处不展开**（04 §四 的三点细节）：
    1. **表格行**（`|` 开头）——表格需要短标识，题号列保持原样；
    2. **附录 A 与题解总览**——那里题号是主键，由调用处按页面路径挡掉；
    3. **代码块内**——按围栏配对跳过，和 `check_prose.py` 同一套判法。

    另有两类**长得像但不是引用**的，正则本身就碰不到：
    题解文件路径（`solutions/nowcoder/BISHI64/sol.py`，题号是路径的一段）
    与链接目标（`](../solutions/BISHI64.md)`，题号在括号里）。
    """
    meta = _state.get("meta") or {}
    out, inside = [], False
    for line in markdown.split("\n"):
        if _FENCE_LINE.match(line):
            inside = not inside
            out.append(line)
            continue
        if inside or line.lstrip().startswith("|"):
            out.append(line)
            continue

        def repl(m):
            no, target = m.group(1), m.group(2)
            title = (meta.get(no) or {}).get("title")
            if not title:
                return m.group(0)
            text, attr = _expand_one(no, title, (meta.get(no) or {}).get("site", ""))
            return f'[{text}]({target} "{attr}")' if attr else f"[{text}]({target})"

        out.append(_PROB_LINK.sub(repl, line))
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# 章首「配套例题」与例题节的清单表（04 号文件 §四 细节 3）
# --------------------------------------------------------------------------- #
#
# 这两块**至今是手写的**：P1② 给 30 章挂了 201 道题，一处都没往章首那行里加，
# 于是 `check_orphan` 一直报「30 章落后、215 个题号没列」。手工补等于给将来多攒债
# （09 教训七：能从权威数据推出来的数字就别写进正文），所以 P-R① 把它整块换成生成。
#
# 形态由用户 2026-08-25 拍板（04 §四 细节 3）：
#
#   章首      只留一句「本章配套 N 道例题，见 §例题」。
#             实测 20 章 ≥7 道、13 章 ≥11 道，最多 31 道（ds/linked-list）——
#             把题名全塞进第一屏，读者还没读到正文就先划过三屏。
#   例题节    一张完整表：题号 · 题名 · 难度 · 题解链接。整章的题在这里一次看全，
#             因为「我要挑题做」这个时刻，人已经在例题节了。
#
# **「详解 / 速览」那一列不在这里生成**：它的值是 P-E 批次的产物（05 §P-E），
# 在那之前既不生成、也不许手工标注（09 教训七）。
#
# 锚点**不猜 slug**：`§例题` 指向的是这里自己发的 `<span id>`，不是那个 `##` 标题的
# 自动 id。pymdownx 的 slugify 直接调用与经 toc 扩展调用对全角空格的处理不一致
# （前者丢弃、后者转成分隔符），而例题节的标题恰好是「N　例题」这种带全角空格的形状。
# 自己发一个 id 就绕开了整件事，也不必碰任何标题文本（09 教训二十八）。
NL = "\n"
_EX_HEAD = re.compile(r"<!--\s*CHAPTER-EXAMPLES\s*-->")
_EX_TABLE = re.compile(r"<!--\s*CHAPTER-EXAMPLE-TABLE\s*-->")
_EX_ANCHOR = "chapter-examples"


def _examples_head(page_id: str, linked: bool) -> str:
    probs = (_state.get("chapter_problems") or {}).get(page_id) or []
    if not probs:
        return ""
    tail = f"，见 [§例题](#{_EX_ANCHOR})。" if linked else "。"
    return f"> **本章配套 {len(probs)} 道例题**{tail}"


def _examples_table(page_id: str, base: str) -> str:
    """题号 · 题名 · 难度 · 题解链接，行序照 `_mapping.json`。

    题号列**保持题号原样**（04 §四 细节 1：表格需要短标识），
    这一点是自动成立的——`_expand_problem_refs()` 跳过 `|` 开头的行。
    """
    probs = (_state.get("chapter_problems") or {}).get(page_id) or []
    if not probs:
        return ""
    meta = _state.get("meta") or {}
    rows = [f'<span id="{_EX_ANCHOR}"></span>', "",
            "| 题号 | 题名 | 难度 | 题解 |", "| --- | --- | --- | --- |"]
    for no in probs:
        m = meta.get(no) or {}
        rows.append("| %s | %s | %s | [题解](%ssolutions/%s.md) |"
                    % (no, m.get("title") or "—", m.get("difficulty") or "—", base, no))
    return NL.join(rows)


_STAT_TOKEN = re.compile(r"<!--\s*N:(chapters|parts|problems|judged|vol[123])\s*-->")


def _stat(name: str) -> str:
    """首页那几个「89 章 / 11 个部分 / 366 题」原先是手写的，写完就开始漂
    （09 教训七点名过它们；P1③ 锁定复核实测「165」比实际少了 201 题）。
    这里从构建期已经算好的 `_state` 里取，正文只留一个 token。
    """
    parts = _state.get("parts") or []
    meta = _state.get("meta") or {}
    if name.startswith("vol"):
        vols = _state.get("volumes") or []
        i = int(name[3:]) - 1
        return str(vols[i][1]) if i < len(vols) else ""
    if name == "parts":
        return str(len(parts))
    if name == "chapters":
        return str(sum(len(ch) for _, _, ch in parts))
    if name == "problems":
        return str(len(meta))
    if name == "judged":
        return str(sum(1 for no in meta
                       if any(k in (meta[no].get("submit") or "") for k in ("通过", "AC"))))
    return ""


def on_page_markdown(markdown, page, config, files):
    src = page.file.src_uri
    # 附录 A 与题解页 / 题解总览里题号是主键，不展开（04 §四 细节 2）
    if not (src.startswith("appendix/") or src.startswith(OUT_DIR + "/")):
        markdown = _expand_problem_refs(markdown)

    markdown = _STAT_TOKEN.sub(lambda m: _stat(m.group(1)), markdown)

    depth = src.count("/")
    base = "../" * depth if depth else ""

    # 章首一句 ＋ 例题节的清单表。两块**都**要有 token 才互相链接：
    # `toolkit/io` 与 `dp/opt/basic` 没有独立的「例题」节，它俩的表就落在章首，
    # 那时章首那句不再往下指（指向紧挨着的自己没有意义）。
    head = _EX_HEAD.search(markdown)
    if head:
        page_id = src[:-3] if src.endswith(".md") else src
        tab = _EX_TABLE.search(markdown)
        # 表落在**另一个 `##` 小节**里，章首那句才往下指；`toolkit/io` 与
        # `dp/opt/basic` 没有独立的「例题」节，表就紧挨在章首，那时不加链接
        # （指向紧挨着的自己没有意义）。判据是两个 token 之间有没有隔着一个 `##`。
        linked = bool(tab) and re.search(
            r"^##\s", markdown[head.end():tab.start()], re.M) is not None
        # 用函数做替换：re.sub 不会对函数的返回值解释  / \g<> 这类转义，
        # 而题名里真的有反斜杠时，字符串替换会当场把它吃掉。
        markdown = _EX_HEAD.sub(lambda m: _examples_head(page_id, linked), markdown, count=1)
        markdown = _EX_TABLE.sub(lambda m: _examples_table(page_id, base), markdown, count=1)

    if "<!-- CHAPTER-MAP" not in markdown:
        return markdown

    # 目录索引页只渲染自己那一个目录，首页渲染全书
    folder = src.split("/")[0] if depth else ""
    only = folder if any(f == folder for f, _, _ in _state["parts"]) else None

    def repl(m):
        return chapter_map(_state["parts"], _state["counts"], base, only)

    return re.sub(r"<!-- CHAPTER-MAP(?::[^>]*)? -->", repl, markdown)
