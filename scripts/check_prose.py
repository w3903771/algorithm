"""正文文风规范的可执行版：把 dev/spec/正文文风规范.md 的条款逐条跑一遍。

输出 `dev/audit/文风校验报告.md`，并生成 00 号文件 §D4 / §D8 的两张数字表。

**只用标准库。** 本脚本进 CI，而 CI 只 `pip install mkdocs-material mkdocs-redirects`
（没有 uv，也没有别的依赖）；要第三方包就得同时改 workflow。

--------------------------------------------------------------------------
为什么有基线，以及它为什么不是「关报警器」
--------------------------------------------------------------------------
现有 89 章是改造前写的，口吻清洗（620 余处）排在 P1①。若让 CI 直接对着条款红着，
下一步只有两条路：关掉规则，或者永远忽略它——两条都等于没有闸门。

改成**棘轮**：`data/_prose_baseline.json` 记下每个「文件 × 条款」的当前处数，
CI 只在**超出基线**时失败。于是：

- 今天全绿，因为基线就是今天的实测；
- 新写的章一旦犯规立刻红——它在基线里是 0；
- 老章被改动时只许减不许增；
- P1① 清洗完跑一次 `--baseline` 把数压下去，**压下去就再也回不来**。

基线里的每一条都是**已登记的待办**，不是「这条规则不算数」。报告把「已知待办」
与「新问题」分开列，就是为了这个区别（08 号文件 §6.2 第 3 点）。

--------------------------------------------------------------------------
本脚本看不见什么
--------------------------------------------------------------------------
1. **CI / 构建配置**。只读 `docs/**/*.md`。`mkdocs.yml`、workflow、hooks 里的问题
   一律不报（P-M① 的两个真缺陷之一就出在这儿）。
2. **只存在于 HTML 属性里的东西**（`href` / `title` / `alt`）。它读 markdown 源码，
   源码里的链接目标能看见；但构建期注入的属性（源码按钮的 GitHub 链接、题号展开写进
   `title` 的题名）它一个字都看不到。那类改动要另扫构建产物。
3. **链接指向的目标存不存在**、锚点对不对。归 `check_links.py`。
4. **代码能不能跑**。归 `verify_docs.py`（本脚本只数代码块，不执行）。
5. **语义**。「很快」能查，「这段话讲错了」查不出来；`_prose_allow.json` 里登记的
   例外只核对「登记过没有」，不核对理由写得对不对。
6. **`solutions/` 与 `dev/`**。前者以 `dev/spec/题解注释规范.md` 为准，
   后者整个不适用（规范 §〇）。
7. **生成页**。带「自动生成」标记的页面整份跳过——它们的内容由脚本负责。
8. **结构体检只看「块的形状」**，不看句子通不通。它能抓「以逗号收尾后面直接是标题」
   与「表格缺表头行」这类**切断**的痕迹，抓不到「这一段搬错了地方」。

用法:
  python scripts/check_prose.py                # 全量校验（CI 跑这个）
  python scripts/check_prose.py --baseline     # 用当前实测重设基线（清洗完才跑）
  python scripts/check_prose.py --sync         # 把 §D4 / §D8 两张表写回 00 号文件
  python scripts/check_prose.py --fix          # 只做零风险自动修（P1 来源行 / P14 句首连接词）
  python scripts/check_prose.py -v             # 逐条打印命中位置
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

REPORT = AUDIT / "文风校验报告.md"
BASELINE = DATA / "_prose_baseline.json"
ALLOW = DATA / "_prose_allow.json"
OVERVIEW = ROOT / "dev" / "plan" / "00-总纲.md"

GENERATED = re.compile(r"自动生成|不要手改")

# --------------------------------------------------------------------------
# 条款。`scope`：prose = 跳过代码块，all = 连代码块一起看（人称与 AI 腔适用于注释）。
# 每条都要能指回 dev/spec/正文文风规范.md 里的编号，否则规范与脚本会各说各话。
# --------------------------------------------------------------------------
RULES = [
    dict(id="P1",  name="章首「来源」行",         scope="prose", fix="line",
         pat=r"^>\s*\*\*来源\*\*"),
    dict(id="P2",  name="内部资料编号 S1–S5",     scope="prose",
         pat=r"(?<![A-Za-z0-9_])S[1-5](?![0-9A-Za-z_])"),
    # P2b 是 P1① 补的（09 教训二十一）：P1/P2/P3 抓的都是**带标识的**出处
    # （`> **来源**` 行、`S1`–`S5`、`模板.docx`）。可「课件」「第 57–60 页」
    # 这类**不带任何标识的**内部来源指代一条都抓不到——读者既拿不到那份课件、
    # 也翻不到那一页，与 `S3 day9` 是同一类东西，只是正则看不见。
    # 实测 P1/P2/P3 清零之后仍剩 117 行 / 21 文件。教训四的形状：
    # 闸门的名字（「内部信息外泄」）承诺得比它检查的多。
    dict(id="P2b", name="无标识的内部来源指代（课件 / 第 N 页）", scope="prose",
         pat=r"课件|第\s*\d+\s*(?:[–—-]\s*\d+\s*)?页"),
    dict(id="P3",  name="具体源文件名",           scope="prose",
         pat=r"day\d+《|\.docx|\.pptx?(?![a-z])|(?<![\w.])\.doc(?![a-z])|useful algorithm"),
    dict(id="P4",  name="外部教程点名",           scope="prose",
         pat=r"菜鸟教程"),
    dict(id="P5",  name="正文引用 dev/ 下的产物", scope="prose",
         pat=r"(?<![\w/])dev/(spec|plan|audit|data|notes)/"),
    dict(id="P5b", name="引用或外链 OI Wiki",     scope="prose",
         pat=r"OI[ -]?[Ww]iki|oi-wiki\.org"),
    dict(id="P5c", name="批次 ID 与决议编号",     scope="prose",
         pat=r"P-M[①②③]|(?<![\w])P[0-6][a-c①-⑧](?![\w])|决议\s*[A-N](?![\w])"),
    dict(id="P6",  name="叙述中的平台名",         scope="prose",
         pat=r"牛客|力扣|洛谷|LeetCode|Codeforces|AtCoder",
         exempt=["appendix/a-problems.md"]),
    dict(id="P7",  name="链接标签带平台名",       scope="prose",
         pat=r"\[[^\]\n]*(牛客|力扣|洛谷)[^\]\n]*\]\(",
         exempt=["appendix/a-problems.md"]),
    dict(id="P10", name="第二人称「你」",         scope="all",
         pat=r"你"),
    # 单字「我」的前后都要排除构词：`自我`（自我惩罚 / 自我松弛）不是第一人称。
    # 中文没有词边界，这条只能靠逐个排除已实测到的构词——**误报比漏报贵**，
    # 因为报告是 P1① 逐条改写的工作单，一条误报就是一次白跑。
    dict(id="P11", name="第一人称「我们 / 我」",  scope="all",
         pat=r"我们|(?<![你他她它自忘无])我(?![们])"),
    dict(id="P12", name="「本书 / 本教程」自指",  scope="prose",
         pat=r"本书|本教程"),
    dict(id="P13", name="叙述写作或调试过程",     scope="prose",
         pat=r"上一版|原本用的|被证伪|这里改过"),
    # P14 的词表分两类，**只有第一类能自动删**：
    #   · 句首空转连接词——整段删掉后半句自己就是结论，删了不影响语法；
    #   · 句中修饰语（不难发现 / 显而易见 / 众所周知）——它们可以出现在句子中间，
    #     「某个**显而易见**的下界」删完变成「某个的下界」，语法直接坏掉。
    # 实测过：`--fix` 一开始把两类一起删，就产出了那句病句。第二类只报告，人来改写。
    dict(id="P14", name="AI 腔 · 句首空转连接词",  scope="all", fix="word",
         pat=r"值得注意的是[，,]?|需要注意的是[，,]?|综上所述[，,]?|总而言之[，,]?|"
             r"总的来说[，,]?|让我们|接下来我们|首先我们|我们可以看到[，,]?|"
             r"在本节中[，,]?|在这一部分[，,]?|如上所述[，,]?"),
    dict(id="P14b", name="AI 腔 · 句中修饰语（只报告）", scope="all",
         pat=r"不难发现|显而易见|众所周知"),
    dict(id="P15", name="无量纲结论",             scope="prose",
         pat=r"很快(?![的地]?[排查看])|效率高|性能不错|差不多"),
    dict(id="T1",  name="Tab 标签不是 C++/Python", scope="all",
         pat=r'^\s*===\s+"(?!C\+\+"|Python")'),
    dict(id="S1",  name="`##` 带章号（应用局部序号）", scope="prose",
         pat=r"^##\s+\d+\.\d"),
    dict(id="S2",  name="`###` 带编号",           scope="prose",
         pat=r"^###\s+\d+[.　 ]"),
    dict(id="S4",  name="跨章引用写了章号",       scope="prose",
         pat=r"\[\d+[-　 ][^\]\n]*\]\([^)\n]*\.md"),
    # 这两条只对**章节文件**成立：目录索引页与附录没有 front-matter，也不该有速查
    # S5 查的是**四个必需字段齐全**，不只是「有没有 front-matter」。
    # 原判据只查 `id:`——P0c 锁定复核发现它比规范松：08 §6.4 的验收写着
    # 「`lang` 与 `volume` 两个字段都写了」，可**没有任何闸门在看那两个字段**，
    # P1① 只写 `id` 也能把 S5 压到 0，然后 P2 因为拿不到 `lang` 当场塌掉（决议 N）。
    # 这是教训四的形状：闸门的名字承诺得比它检查的多。
    #   id     章的唯一键，_topics/_mapping/附录/跨章引用全以它为键（02 §三）
    #   title  中文标题（02 §三）
    #   volume 1|2|3，三卷只活在 nav 与 front-matter（02 §2.4）
    #   lang   py|cpp，主轨由它声明、不靠文件名猜（决议 N，04 §1.4）
    # 四个前瞻各自被 `(?!---\n)` 挡在 front-matter 块内，掉到正文里的不算。
    # `prereq` 是选填，它的 id 存不存在归 check_links，不在这里查。
    #
    # **`.cpp.md` 附轨页豁免**：04 §1.4 明写附轨页「写 `lang: cpp`，并且**不写 `volume`**」
    # （卷归属只由主轨声明，避免两处打架），拿主轨的四字段去要求它必然误报。
    # 附轨页的 front-matter 归 `check_dual.py`（P2 交付，04 §五 的验收表已列）。
    # 现在附轨页是 0 个，这条豁免是给 P2 提前铺的——等 P2 造出 36 页再发现就晚了。
    dict(id="S5",  name="front-matter 必需字段不全", scope="file", only="chapter",
         exempt=[".cpp.md"],
         pat=r"\A---\n"
             r"(?=(?:(?!---\n)[^\n]*\n)*?id:\s*\S)"
             r"(?=(?:(?!---\n)[^\n]*\n)*?title:\s*\S)"
             r"(?=(?:(?!---\n)[^\n]*\n)*?volume:\s*[123]\b)"
             r"(?=(?:(?!---\n)[^\n]*\n)*?lang:\s*(?:py|cpp)\b)"),
    dict(id="R5",  name="缺「本章速查」收尾",     scope="file", only="chapter",
         pat=r"^#{2,3}\s*.*本章速查"),
]

# 结构体检（教训八）：四道闸门都不看句子完整性，按行号切正文会在块中间断开。
STRUCT = [
    ("SC1", "段落截断（以逗号/顿号收尾，后面直接是分隔线或标题）"),
    ("SC2", "代码围栏个数为奇数"),
    ("SC3", "文件以引用块结尾"),
    # 说明文字会被原样写进报告的表格单元格里，**不能含裸的 `|`**——
    # 原文写的是「`| --- |` 上面不是表格行」，那一行因此有 7 个竖线而不是 5 个，
    # 把「逐条现状」整张表撑坏了，而九个闸门一条都不报（09 教训四十）。
    ("SC4", "表格缺表头行（分隔行 `---` 上面不是表格行）"),
    ("SC5", "引用块中间掉了 `>` 前缀（靠惰性续行撑着）"),
]

FENCE = re.compile(r"^\s*(```|~~~)")


def chapter_files() -> list:
    """章节文件：`docs/**/*.md` 去掉 `appendix/` 与 `index.md`。

    这是 00 号文件 §D4 那张表的口径，写死在这里而不是散在调用处——
    口径一旦有第二份实现，两张表就会开始打架。
    """
    return [p for p in sorted(DOCS.rglob("*.md"))
            if p.name != "index.md" and "appendix" not in p.relative_to(DOCS).parts]


def all_files() -> list:
    out = []
    for p in sorted(DOCS.rglob("*.md")):
        head = "\n".join(p.read_text(encoding="utf-8").splitlines()[:8])
        if not GENERATED.search(head):
            out.append(p)
    return out


# front-matter 是 P1① 给 89 章补的**机器可读元信息**，不是正文。
# 它一进来就给「正文命中数」注了水：`title: 线段树` / `id: ds/segment-tree`
# 会被按关键词计数的脚本当成「这一章讲了线段树」——实测 69 条知识点被注水 87 处
# （09 教训二十二）。凡是拿正文命中数当**依据**的地方，都要先剥掉它。
# 口径放在这里而不是各脚本里各写一遍：check_prose 是「什么算正文」的归口
# （`chapter_files()` 定章集合、`prose_lines()` 定跳不跳代码块），
# `audit_topics.py` / `audit_depth.py` 都 import 本函数。
_FRONT_MATTER = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.S)


def strip_front_matter(body: str) -> str:
    """剥掉开头的 YAML front-matter；没有就原样返回。"""
    return _FRONT_MATTER.sub("", body, count=1)


def prose_lines(body: str) -> list:
    """`[(行号, 文本, 是否在代码块内)]`。跳代码块靠围栏配对，不靠缩进。"""
    out, inside = [], False
    for i, ln in enumerate(body.splitlines(), 1):
        if FENCE.match(ln):
            inside = not inside
            out.append((i, ln, True))
            continue
        out.append((i, ln, inside))
    return out


def load_allow() -> dict:
    """`{条款: {文件: [登记过的原句片段]}}`——规范 §2.2 要求例外逐条登记。"""
    if not ALLOW.exists():
        return {}
    return json.loads(ALLOW.read_text(encoding="utf-8"))


def scan_rules(files: list) -> dict:
    """`{条款: {文件: [(行号, 命中文本)]}}`。"""
    allow = load_allow()
    chapters = {p.relative_to(ROOT).as_posix() for p in chapter_files()}
    hits: dict = {r["id"]: {} for r in RULES}
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        short = p.relative_to(DOCS).as_posix()
        body = p.read_text(encoding="utf-8")
        lines = prose_lines(body)
        for r in RULES:
            if any(short.endswith(e) for e in r.get("exempt", [])):
                continue
            if r.get("only") == "chapter" and rel not in chapters:
                continue
            pat = re.compile(r["pat"], re.M)
            if r["scope"] == "file":
                if not pat.search(body):
                    hits[r["id"]].setdefault(rel, []).append((0, "整份文件"))
                continue
            ok = allow.get(r["id"], {}).get(short, [])
            for no, ln, in_code in lines:
                if in_code and r["scope"] == "prose":
                    continue
                for m in pat.finditer(ln):
                    if any(frag and frag in ln for frag in ok):
                        continue
                    hits[r["id"]].setdefault(rel, []).append((no, m.group(0)))
    return hits


def scan_struct(files: list) -> dict:
    """结构体检。只看块的形状，抓的是「按行号切正文」留下的断口。"""
    hits: dict = {k: {} for k, _ in STRUCT}
    tail = re.compile(r"[，、,；;]\s*$")
    row = re.compile(r"^\s*\|.*\|\s*$")
    sep = re.compile(r"^\s*\|(\s*:?-{2,}:?\s*\|)+\s*$")
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        lines = p.read_text(encoding="utf-8").splitlines()
        flags = [False] * len(lines)          # 是否在代码块内
        inside = False
        n_fence = 0
        for i, ln in enumerate(lines):
            if FENCE.match(ln):
                inside = not inside
                n_fence += 1
            flags[i] = inside
        if n_fence % 2:
            hits["SC2"].setdefault(rel, []).append((0, f"{n_fence} 个围栏"))

        for i, ln in enumerate(lines):
            if flags[i]:
                continue
            if tail.search(ln):
                nxt = next((x for x in lines[i + 1:] if x.strip()), "")
                if nxt.startswith("#") or re.match(r"^\s*-{3,}\s*$", nxt) or not nxt:
                    hits["SC1"].setdefault(rel, []).append((i + 1, ln.strip()[-24:]))
            if sep.match(ln) and not (i and row.match(lines[i - 1]) and not sep.match(lines[i - 1])):
                hits["SC4"].setdefault(rel, []).append((i + 1, ln.strip()))

        last = next((x for x in reversed(lines) if x.strip()), "")
        if last.startswith(">"):
            hits["SC3"].setdefault(rel, []).append((len(lines), last.strip()[:24]))

        # SC5：引用块中间掉了 `>`（09 号文件 教训四十）。
        # CommonMark 的**惰性续行**会把这样的行仍然收进引用块，所以渲染出来往往
        # 是对的——`mkdocs build --strict` 与 SC1–SC4 一条都不报。但它是靠一条
        # 脆弱的规则撑着：只要上一行改成列表项、表格行，或中间多出一个空行，
        # 这段就会当场掉出引用框。**写的是承诺，撑住它的是巧合。**
        #
        # 判据是「一段**连续**的非 `>` 非空行夹在两段 `>` 之间」，不是三行窗口——
        # `set.md:512-513` 这个活样本恰好断了**两行**，三行窗口报不出它（教训十八：
        # 反过来验证，别问「我写了吗」，问「本该命中的样本命中了吗」）。
        i = 0
        while i < len(lines):
            if flags[i] or not lines[i].lstrip().startswith(">"):
                i += 1
                continue
            j = i + 1
            while (j < len(lines) and not flags[j] and lines[j].strip()
                   and not lines[j].lstrip().startswith(">")):
                j += 1
            if j > i + 1 and j < len(lines) and not flags[j] \
                    and lines[j].lstrip().startswith(">"):
                hits["SC5"].setdefault(rel, []).append(
                    (i + 2, lines[i + 1].strip()[:24]))
            i = j
    return hits


# --------------------------------------------------------------- 数字表

def code_stats() -> dict:
    """00 号文件 §D8 的三个数。**每一个都要能点名出处**（教训十一）。

    「已验证」那一档不自己重算，直接调 `verify_docs.executable_sections()`——
    抽取口径只有那一份实现，两处各写一遍必然漂移。
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    import verify_docs                                   # 只用标准库，CI 里 import 得到

    verified = {(md.as_posix(), code) for md, _, code in verify_docs.executable_sections()}
    total = frag = ver = 0
    for p in sorted(DOCS.rglob("*.md")):
        lines = p.read_text(encoding="utf-8").splitlines()
        i = 0
        while i < len(lines):
            if lines[i].startswith("```python"):        # 口径：顶格起始的 python 块
                total += 1
                j = i + 1
                while j < len(lines) and not re.match(r"^```\s*$", lines[j]):
                    j += 1
                code = "\n".join(lines[i + 1:j]) + "\n"
                if "# [片段]" in code:
                    frag += 1
                elif (p.as_posix(), code) in verified:
                    ver += 1
                i = j + 1
            else:
                i += 1
    return {"total": total, "frag": frag, "verified": ver,
            "rest": total - frag - ver}


def d4_table(hits: dict, files: list) -> list:
    """§D4：口吻与措辞。口径与首测同为「章节文件」，不含 appendix/ 与 index.md。"""
    keep = {p.relative_to(ROOT).as_posix() for p in files}
    # 「首测」是 P-M① 之前的一次人工统计，口径比现在窄，逐行标出是哪一个词
    rows = [
        ("章首 `> **来源**：…` 行", "P1", "71", "暴露内部资料链路，读者不需要也看不到"),
        ("`S1`–`S5` 内部编号", "P2", "242 / 54 文件", "外部读者完全无法解析"),
        ("「菜鸟教程」", "P4", "20", "掉价；且部分是「菜鸟教程上那种写法」的贬低式引用"),
        ("平台名（牛客 / 力扣 / 洛谷 …）", "P6", "只数「牛客」：267 / 78 文件",
         "平台名反复出现，读起来像平台软文"),
        ("第二人称「你」", "P10", "44", "与 `题解注释规范`「不用第一/第二人称」冲突"),
        ("第一人称「我们 / 我」", "P11", "只数「我们」：21", "同上"),
        ("「本书 / 本教程」自指", "P12", "只数「本书」：2", "同上"),
        # 一行可以对应多条条款：P14 拆成「句首连接词」＋「句中修饰语」之后，
        # 这一行若只取 P14 就会显示 0，而实际还有 2 处——**拆规则时最容易漏掉的就是这里**。
        ("AI 腔词表（P14 ＋ P14b）", ("P14", "P14b"), "0",
         "首测漏了「不难发现 / 显而易见」两处，并非已达标"),
    ]
    out = ["| 现象 | 处数 | 文件数 | 首测（P-M① 前） | 问题 |",
           "| --- | --- | --- | --- | --- |"]
    for name, rid, first, note in rows:
        ids = rid if isinstance(rid, tuple) else (rid,)
        by_file: dict = {}          # 别叫 files——那是本函数的入参（章节文件列表）
        for one in ids:
            for k, v in hits.get(one, {}).items():
                if k in keep:
                    by_file.setdefault(k, []).extend(v)
        n = sum(len(v) for v in by_file.values())
        out.append(f"| {name} | **{n}** | {len(by_file)} | {first} | {note} |")
    out += ["",
            f"口径：`docs/` 下 **{len(files)} 个章节文件**（不含 `appendix/`、不含 `index.md`）。",
            "人称与 AI 腔连代码注释一起数，其余条款跳过代码块。",
            "「首测」那一列的口径更窄，逐行已标明——**两列不能直接相减**。"]
    pat = re.compile(r"(?<![A-Za-z0-9])(BISHI|PIO|BM|LC)(\d+)(?![0-9])")
    cnt: dict = {}
    for p in files:
        for m in pat.finditer(p.read_text(encoding="utf-8")):
            cnt[m.group(1)] = cnt.get(m.group(1), 0) + 1
    tot = sum(cnt.values())
    out += ["", f"正文里的内部题号引用共 **{tot}** 处（"
                + "、".join(f"`{k}*` {cnt.get(k, 0)}" for k in ("BISHI", "PIO", "BM", "LC"))
                + "）。"]
    return out


def d8_table(st: dict) -> list:
    return ["| 档 | 段数 | 出处 |", "| --- | --- | --- |",
            f"| 正文 Python 代码块（顶格 ```` ```python ````） | **{st['total']}** | 本脚本实测 |",
            f"| 其中标了 `# [片段]` 主动豁免 | **{st['frag']}** | 本脚本实测 |",
            f"| 其中已由 `verify_docs.py` 跑过官方样例 | **{st['verified']}** | "
            f"`verify_docs.executable_sections()`，与 `dev/audit/正文代码验证报告.md` 同源 |",
            f"| **既非片段、也未验证** | **{st['rest']}** | 前三行的差集 |"]


MARK = "<!-- {}:{} 由 scripts/check_prose.py --sync 生成，不要手改 -->"


def sync_overview(d4: list, d8: list) -> bool:
    """把两张表写回 00 号文件的标记区间。数字能推出来就别手写（教训七）。"""
    body = OVERVIEW.read_text(encoding="utf-8")
    changed = False
    for tag, table in (("D4", d4), ("D8", d8)):
        b, e = MARK.format(tag, "BEGIN"), MARK.format(tag, "END")
        if b not in body or e not in body:
            print(f"[跳过] 00 号文件里没有 {tag} 的标记区间")
            continue
        head, rest = body.split(b, 1)
        _, tail = rest.split(e, 1)
        new = head + b + "\n\n" + "\n".join(table) + "\n\n" + e + tail
        changed |= new != body
        body = new
    if changed:
        OVERVIEW.write_text(body, encoding="utf-8")
    return changed


def overview_stale(d4: list, d8: list) -> bool:
    """§D4 / §D8 两张表跟实测对不对得上。

    **总纲不在就跳过这一项。** 它是开发侧文档，公开检出里没有；
    而这一项检查的是「方案文件里的数字表有没有过期」，与 27 条条款
    一条都不相干——本脚本的正事（棘轮 ＋ 结构体检）在没有它时照样跑得完整。
    不加这个判空，公开仓的 CI 会在一个与文风无关的理由上整条挂掉。
    """
    if not OVERVIEW.exists():
        return False
    body = OVERVIEW.read_text(encoding="utf-8")
    for tag, table in (("D4", d4), ("D8", d8)):
        b, e = MARK.format(tag, "BEGIN"), MARK.format(tag, "END")
        if b not in body or e not in body:
            return True
        cur = body.split(b, 1)[1].split(e, 1)[0].strip()
        if cur != "\n".join(table).strip():
            return True
    return False


# --------------------------------------------------------------- 自动修

# 句读：句首连接词只在这些位置之后才允许自动删。
# 「行首」与「句号/分号/冒号之后」是安全的，句子中间不是——
# 中间那一处删完会把前后两半接成病句，而正文没有回归测试兜底。
SENT_START = re.compile(r"(\A|(?<=[。；！？：])|(?<=^> )|(?<=^\- )|(?<=^\* ))")


def autofix(files: list) -> int:
    """`--fix` 的边界：**只允许整行删除，与句首位置的词表删除**。

    需要改写句子的（P2 句中编号、P6 叙述性平台名、P10–P12 人称）一律只报告不改写——
    自动改写句子是在正文里制造新缺陷，而正文没有回归测试。

    词表删除还要再收一道：**只删句首的那一处**。P14 的词表里既有句首连接词
    （「值得注意的是，」删掉后半句自己就是结论），也有句中修饰语——后者已拆到
    P14b 只报告不改。但连接词本身也可能出现在句中，所以位置仍要判。

    **「整行删除」删的是条目，不是行**（09 教训八：按块切不按行号切）。P1 的
    `> **来源**：…` 是引用块里的一个条目，实测 82 处里有 **10 处折了行**——
    只删正则命中的那一行，会在页面上留下一条无主的续行
    （`> 「倍增 LCA」与「RMQ」两节`），而四道闸门加 SC1–SC4 一条都不报。
    所以命中之后要把**续行一并吃掉**：仍是引用行、且没有起新的 `> **X**：` 条目。
    """
    line_rules = [re.compile(r["pat"]) for r in RULES if r.get("fix") == "line"]
    word_rules = [re.compile(r["pat"]) for r in RULES if r.get("fix") == "word"]
    quote_item = re.compile(r"^>\s*\*\*")
    n = 0
    for p in files:
        lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
        out = []
        skip = 0
        for i, ln in enumerate(lines):
            if skip:
                skip -= 1
                continue
            if any(r.search(ln) for r in line_rules):
                n += 1
                if ln.lstrip().startswith(">"):
                    j = i + 1
                    while (j < len(lines) and lines[j].lstrip().startswith(">")
                           and not quote_item.match(lines[j])
                           and lines[j].strip() != ">"):
                        j += 1
                    skip = j - i - 1
                continue
            new = ln
            for r in word_rules:
                # 逐个命中判位置：前面必须是行首或句读，否则原样留着让人改
                res, last = [], 0
                for m in r.finditer(new):
                    head = new[:m.start()].lstrip("> -*#").strip()
                    if head == "" or head[-1] in "。；！？：":
                        res.append(new[last:m.start()])
                        last = m.end()
                if res:
                    res.append(new[last:])
                    new = "".join(res)
            if new != ln:
                n += 1
            out.append(new)
        joined = "".join(out)
        if joined != "".join(lines):
            p.write_text(joined, encoding="utf-8")
    return n


# --------------------------------------------------------------- 主流程

def main(argv: list) -> int:
    verbose = "-v" in argv
    files = all_files()
    chapters = chapter_files()

    if "--fix" in argv:
        n = autofix(files)
        print(f"自动修 {n} 处（只做整行删除与词表删除）")
        return 0

    hits = scan_rules(files)
    hits.update(scan_struct(files))
    counts = {rid: {f: len(v) for f, v in d.items()} for rid, d in hits.items()}

    if "--baseline" in argv:
        BASELINE.write_text(json.dumps(
            {"_comment": "check_prose.py 的棘轮基线：{条款: {文件: 处数}}。"
                         "只许减不许增；清洗完一批就跑一次 --baseline 把数压下去。"
                         "基线里的每一条都是已登记的待办，不是「这条规则不算数」。"
                         "键是仓库相对路径；写回时按磁盘剔一遍失效键——"
                         "改名/拆章会让旧键永远留在这里（09 号文件 教训六）。",
             "counts": {rid: {f: n for f, n in d.items() if (ROOT / f).is_file()}
                        for rid, d in counts.items()}},
            ensure_ascii=False, indent=1, sort_keys=True) + "\n",
            encoding="utf-8")
        print(f"基线已重设：{sum(sum(d.values()) for d in counts.values())} 处")

    base = {}
    if BASELINE.exists():
        base = json.loads(BASELINE.read_text(encoding="utf-8")).get("counts", {})

    # 基线以**路径**为键，而改名 / 拆章是这个仓库的常态（P-M① 改过 74 章的名，
    # P1 拆章、P6 重排还会再来）。旧键不会自己消失，新文件在基线里是 0——
    # 于是「文件被改名」的症状是：一边冒出一堆超出基线，一边留下一堆死键。
    # 静默处理会让棘轮悄悄失真，所以两件事都做：报出来，并在 --baseline 时剔掉
    # （09 号文件 教训六、§5.3 教训十二）。
    stale = sorted({f for d in base.values() for f in d
                    if not (ROOT / f).is_file()})

    over, known = [], 0
    for rid, d in counts.items():
        for f, n in sorted(d.items()):
            b = base.get(rid, {}).get(f, 0)
            if n > b:
                over.append((rid, f, b, n))
            known += min(n, b)

    stats = code_stats()
    d4, d8 = d4_table(hits, chapters), d8_table(stats)
    if "--sync" in argv:
        print("00 号文件的 §D4 / §D8 " + ("已更新" if sync_overview(d4, d8) else "无变化"))
        stale_doc = False
    else:
        stale_doc = overview_stale(d4, d8)

    # ---- 报告
    AUDIT.mkdir(parents=True, exist_ok=True)
    total = sum(sum(d.values()) for d in counts.values())
    L = ["# 文风校验报告", "",
         "> 由 `scripts/check_prose.py` 生成，条款正本在 `dev/spec/正文文风规范.md`。",
         "> **不要手改本文件。**", "",
         f"命中 **{total}** 处：已登记待办 **{known}**、**超出基线 {len(over)} 条**。",
         f"章节文件 {len(chapters)} 个，参与校验的页面 {len(files)} 个。", ""]
    if over:
        L += ["## 超出基线（新问题）", "",
              "基线在 `data/_prose_baseline.json`，只许减不许增。", "",
              "| 条款 | 文件 | 基线 | 现在 |", "| --- | --- | --- | --- |"]
        L += [f"| {r} | `{f}` | {b} | **{n}** |" for r, f, b, n in over]
    else:
        L += ["## 超出基线（新问题）", "", "无。"]
    L.append("")

    if stale:
        L += ["## 基线里的死键", "",
              "这些文件在基线里有记录，磁盘上却不存在了——**被改名或删除**。",
              "基线以路径为键，旧键不会自己消失（09 号文件 教训六）。",
              "确认改名无误后跑一次 `--baseline` 把它们剔掉。", ""]
        L += [f"- `{f}`" for f in stale] + [""]

    L += ["## 逐条现状", "", "| 条款 | 说明 | 处数 | 文件数 | 基线 |",
          "| --- | --- | --- | --- | --- |"]
    names = {r["id"]: r["name"] for r in RULES}
    names.update(dict(STRUCT))
    for rid in list(names):
        d = counts.get(rid, {})
        n = sum(d.values())
        b = sum(base.get(rid, {}).values())
        L.append(f"| {rid} | {names[rid]} | {n} | {len(d)} | {b} |")
    L.append("")

    L += ["## 结构体检明细", "",
          "四道闸门都不看句子完整性——按行号切正文会在块中间断开，"
          "`mkdocs build` / `check_links` / `verify_docs` / `diff_build` 一条都不报。", ""]
    detail = [(k, f, v) for k, _ in STRUCT for f, v in sorted(hits.get(k, {}).items())]
    if detail:
        L += ["| 项 | 文件 | 位置 |", "| --- | --- | --- |"]
        L += [f"| {k} | `{f}` | {'；'.join(f'{ln}: `{t}`' for ln, t in v[:4])} |"
              for k, f, v in detail]
    else:
        L.append("零断口。")
    L += ["", "## 00 号文件 §D4　口吻与措辞", ""] + d4
    L += ["", "## 00 号文件 §D8　正文代码的验证覆盖", ""] + d8 + [""]
    REPORT.write_text("\n".join(L), encoding="utf-8")

    if verbose:
        for rid, d in hits.items():
            for f, v in sorted(d.items()):
                for ln, t in v:
                    print(f"[{rid}] {f}:{ln}  {t}")
    for r, f, b, n in over:
        print(f"[超出基线] {r} {f}：{b} -> {n}")
    if stale_doc:
        print("[过期] 00 号文件的 §D4 / §D8 与实测不一致，跑 --sync")
    if stale:
        print(f"[基线有死键] {len(stale)} 个文件已改名或删除：{stale[:5]}"
              "　→ 确认改名无误后跑一次 --baseline 把它们剔掉")

    print(f"\n命中 {total} 处：已登记待办 {known}、超出基线 {len(over)} 条")
    print(f"报告：{REPORT.relative_to(ROOT)}")
    return 1 if (over or stale_doc) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
