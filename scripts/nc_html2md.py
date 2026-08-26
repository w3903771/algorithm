"""牛客题面 HTML -> Markdown 的转换工具。

牛客把所有公式渲染成 <img alt="LaTeX" src=".../equation?tex=...">，
其中相当一部分是纯排版占位（\\hspace{...}、\\bullet 项目符号），要区别处理。
"""
from __future__ import annotations

import re
from urllib.parse import unquote

from bs4 import BeautifulSoup, NavigableString, Tag

# 间距宏（纯排版占位）。牛客用它们做缩进和项目符号的对齐。
# 注意：只能「整条公式除了间距宏什么都不剩」时才判为排版，不能只看开头——
# 题面里大量真公式形如 `\quad 2 \cdot \sum ... > \sum ...`，
# 早期版本按前缀匹配，把这些公式整条丢掉了（BISHI40 的两条核心约束因此消失）。
_SPACING = re.compile(
    r"\\(?:hspace|vspace|phantom|hskip|kern)\s*\{[^}]*\}"      # \hspace{15pt}
    r"|\\(?:quad|qquad|hfill|thinspace|enspace|;|:|!|,)"        # \quad \, \; ...
    r"|\\\s"                                                    # 反斜杠 + 空格
)
_BULLET = re.compile(r"^\\(?:bullet|cdot|circ)\b")
_NUMBERED = re.compile(r"_\\texttt\{(\d+)\.\}")


def _formula_of(node: Tag) -> str:
    """取公式图片的 LaTeX 源码。

    优先从 src 的 `equation?tex=<urlencoded>` 里取，而不是 alt 属性：
    题面里出现 \\texttt{"Yes"} 这类含双引号的公式时，HTML 的 alt="..." 会被引号
    提前截断（BISHI55 的输出描述就因此丢失了 Yes/No），而 src 里是 URL 编码的，不受影响。
    """
    src = node.get("src") or ""
    m = re.search(r"[?&]tex=([^&]*)", src)
    if m:
        try:
            tex = unquote(m.group(1))
            if tex.strip():
                return tex
        except Exception:
            pass
    return node.get("alt", "")


def _img_to_text(tex: str) -> str:
    """把公式的 LaTeX 源码转成 Markdown。

    三种情形：
      1. 形如 `{\\hspace{20pt}}_\\texttt{1.}\\,` —— 有序列表项标号
      2. 去掉全部间距宏后什么都不剩（或只剩 \\bullet）—— 纯排版占位 / 项目符号
      3. 其余 —— 真公式，剥掉前导间距宏后用 $...$ 包起来
    """
    tex = (tex or "").strip()
    if not tex:
        return ""

    m = _NUMBERED.search(tex)
    if m:
        return "\n{}. ".format(m.group(1))

    # 剥掉所有间距宏，再清掉因此产生的空花括号组，看还剩什么
    core = _SPACING.sub("", tex)
    core = re.sub(r"\{\s*\}", "", core).strip()      # `{\hspace{22.5pt}}` -> `{}` -> 去掉
    core = re.sub(r"\\\s*$", "", core).strip()       # 去掉行尾孤立的反斜杠（`\bullet\` 的尾巴）
    if not core or core in ("{", "}"):
        return ""

    if _BULLET.match(core):
        rest = _BULLET.sub("", core, count=1).strip().lstrip("\\").strip()
        # 「项目符号 + 正文公式」是同一张图时，符号与公式都要保留
        return "\n- " + ("${}$".format(rest) if rest else "")

    return "${}$".format(core)


def _inline(node) -> str:
    """把一个节点的内容转成行内 Markdown 文本。"""
    if isinstance(node, NavigableString):
        return str(node)
    if not isinstance(node, Tag):
        return ""
    name = node.name.lower()
    if name == "img":
        return _img_to_text(_formula_of(node))
    if name == "br":
        return "\n"
    if name in ("b", "strong"):
        inner = "".join(_inline(c) for c in node.children).strip()
        return f"**{inner}**" if inner else ""
    if name in ("i", "em"):
        inner = "".join(_inline(c) for c in node.children).strip()
        return f"*{inner}*" if inner else ""
    if name == "code":
        inner = "".join(_inline(c) for c in node.children).strip()
        return f"`{inner}`" if inner else ""
    if name == "li":
        inner = "".join(_inline(c) for c in node.children).strip()
        return f"\n- {inner}"
    if name == "p":
        inner = "".join(_inline(c) for c in node.children).strip()
        return f"\n\n{inner}"
    if name == "table":
        return "\n" + _table(node) + "\n"
    return "".join(_inline(c) for c in node.children)


def _table(node: Tag) -> str:
    rows = []
    for tr in node.find_all("tr"):
        cells = [" ".join(_inline(td).split()) for td in tr.find_all(["td", "th"])]
        if cells:
            rows.append(cells)
    if not rows:
        return ""
    n = max(len(r) for r in rows)
    rows = [r + [""] * (n - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join(["---"] * n) + " |"]
    for r in rows[1:]:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def tidy(text: str) -> str:
    text = text.replace("\u00a0", " ").replace("\r", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # 列表项前保证独立成行
    text = re.sub(r"(?<!\n)\n- ", "\n\n- ", text)
    return text.strip()


def html_to_md(node) -> str:
    """块级转换：把一个容器节点整体转成 Markdown。"""
    if node is None:
        return ""
    return tidy("".join(_inline(c) for c in node.children))


def pre_to_text(node: Tag) -> str:
    """<pre> 内容 -> 纯文本（公式转成 $..$，<br> 转换行）。"""
    if node is None:
        return ""
    out = "".join(_inline(c) for c in node.children)
    return out.replace("\u00a0", " ").replace("\r", "").strip("\n").rstrip()


def parse_subject(html: str) -> dict:
    """解析 /questionTerminal/<uuid> 页面，返回题面各部分。"""
    soup = BeautifulSoup(html, "lxml")
    box = soup.select_one(".subject-box")
    if box is None:
        return {}

    title_el = box.select_one(".subject-title .js-title") or box.select_one(".subject-title")
    title = " ".join(title_el.get_text(" ", strip=True).split()) if title_el else ""
    title = re.sub(r"^\[.*?\]\s*", "", title)

    limits = ""
    ex = box.select_one(".subject-explain")
    if ex:
        parts = [s.strip() for s in ex.get_text("\n", strip=True).split("\n")
                 if ("限制" in s or "指数" in s)]
        limits = "；".join(parts)

    des = box.select_one(".subject-des") or box
    body = des.select_one(".nc-post-content")
    description = html_to_md(body) if body else ""

    # 输入/输出描述：h5 后紧跟的 pre
    io_desc = {}
    for h5 in des.find_all("h5"):
        label = h5.get_text(strip=True).rstrip(":：")
        pre = h5.find_next_sibling("pre")
        if pre is None:
            nxt = h5.find_next_sibling()
            pre = nxt.find("pre") if isinstance(nxt, Tag) else None
        if pre is not None:
            io_desc[label] = pre_to_text(pre)

    # 示例
    examples = []
    for oi in des.select(".question-oi"):
        hd = oi.select_one(".question-oi-hd")
        name = hd.get_text(strip=True) if hd else f"示例{len(examples)+1}"
        item = {"name": name, "input": "", "output": "", "note": ""}
        for mod in oi.select(".question-oi-mod"):
            h2 = mod.find("h2")
            cont = mod.select_one(".question-oi-cont pre") or mod.select_one(".question-oi-cont")
            key = h2.get_text(strip=True) if h2 else ""
            val = pre_to_text(cont) if cont else ""
            if "输入" in key:
                item["input"] = val
            elif "输出" in key:
                item["output"] = val
            elif "说明" in key:
                item["note"] = tidy(val)
        examples.append(item)

    return {
        "title": title,
        "limits": limits,
        "description": description,
        "inputDesc": io_desc.get("输入描述", ""),
        "outputDesc": io_desc.get("输出描述", ""),
        "otherDesc": {k: v for k, v in io_desc.items() if k not in ("输入描述", "输出描述")},
        "examples": examples,
    }
