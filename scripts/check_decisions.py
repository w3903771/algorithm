"""把决议表逐条变成断言跑一遍，输出 dev/audit/决议落实核对.md。

决议的**正本**是 `dev/notes/拆分点.md` 的「决议记录」汇总表；
**断言**在 `dev/data/_decisions.json`。本脚本做两件事：

1. 核对两边的决议 id 集合一致——汇总表加了一行却没写断言，会被报出来；
2. 逐条跑断言，任何一条不过就退出码非零。

为什么要有这个脚本：决议表有正本、有指针传递、有 commit message 声明执行，
就是没有验收载体。P-M② 收尾时靠「回想一遍，都做了」自查，漏掉了决议 F 的后半句
（「三章各留一句指向」一句没写），锁定复核改成逐条写断言才抓到。

**带「各留一句指向」的决议必须写成 `each_contains`**：断言是「N 个文件都命中」，
不是「至少一个命中」。只查 dp/basic 有没有那一节的话，P-M② 那次照样查不出问题。

只收「当前状态自洽」的断言。依赖一次性基线的那类（比对迁移前的构建快照、
`git diff <迁移前提交>`）跑一次就永远失效，不进这里，留在批次小结里。

--------------------------------------------------------------------------
本脚本看不见什么
--------------------------------------------------------------------------
1. **决议本身对不对**。它只检查「决议说的事做了没有」，不检查「这么定合不合理」。
2. **写不出断言的决议**。汇总表里每条都必须在 `_decisions.json` 有映射，
   但映射写得敷衍（比如只查一个无关的关键词）它分辨不出来——
   断言的质量靠人写，脚本只保证它跑过。
3. **正文的语义**。`contains` 命中的是正则，不是「这句话说得对」。
   决议 B 要求「各留一句指向」，脚本能确认四章都有那个链接，
   不能确认那句话读起来通顺、放的位置合适。
4. **决议之外的改动**。它是一张白名单式的检查表，不是回归测试：
   某章被误删一节而没有任何决议提到它，这里一个字都不会报。
5. **构建期才成立的事**。断言全部读源文件，不跑 `mkdocs build`。
   链接目标存不存在归 `check_links.py`，锚点归它，不归这里。

用法: uv run python scripts/check_decisions.py
      uv run python scripts/check_decisions.py -v    # 连通过的断言一起打印
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DATA = ROOT / "data"        # 公开数据：站点构建与 check_prose 要读，随仓库发布
DEV_DATA = ROOT / "dev" / "data"   # 开发侧数据：不随本仓库发布，clone 的检出里没有这个目录
AUDIT = ROOT / "dev" / "audit"      # 脚本生成的报告：P-M② 起在 dev/audit/（02 §7.3）

REPORT = AUDIT / "决议落实核对.md"
SPEC = DEV_DATA / "_decisions.json"

sys.path.insert(0, str(ROOT / "scripts"))
import sol_store  # noqa: E402


# --------------------------------------------------------------- 文本工具

_cache: dict = {}


def text(rel: str) -> str | None:
    """读仓库相对路径的全文，读不到回 None（断言据此报「文件不存在」）。"""
    if rel not in _cache:
        p = ROOT / rel
        _cache[rel] = p.read_text(encoding="utf-8") if p.is_file() else None
    return _cache[rel]


def section_of(body: str, heading: str) -> str:
    """截出某个 `##` 小节的正文（到下一个同级或更高级标题为止）。

    标题按「包含」匹配，因为 `##` 前面带局部序号（`## 4　DAG 上的 DP`），
    序号会随拆分变动，写死进断言等于给自己埋一颗定时炸弹。
    """
    lines = body.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith("## ") and heading in ln:
            start = i
            break
    if start is None:
        return ""
    for j in range(start + 1, len(lines)):
        if re.match(r"^#{1,2} ", lines[j]):
            return "\n".join(lines[start:j])
    return "\n".join(lines[start:])


def mapping() -> dict:
    return json.loads((DATA / "_mapping.json").read_text(encoding="utf-8"))["chapters"]


# --------------------------------------------------------------- 结构性探针

def probe_layout(_a: dict) -> tuple[bool, str]:
    sol = ROOT / "solutions"
    stray = sorted(p.name for p in sol.glob("*.py"))
    by_site: dict = {}
    for p in sol.glob("*/*/meta.json"):
        by_site[p.parent.parent.name] = by_site.get(p.parent.parent.name, 0) + 1
    total = sum(by_site.values())
    dist = "、".join(f"{k} {v}" for k, v in sorted(by_site.items()))
    if stray:
        return False, f"顶层还有散落的题解：{stray[:5]}"
    return total > 0, f"{total} 题（{dist}），顶层无散落 .py"


def probe_pair(_a: dict) -> tuple[bool, str]:
    sol = ROOT / "solutions"
    bad = []
    for meta in sol.glob("*/*/meta.json"):
        if not (meta.parent / "sol.py").exists():
            bad.append(meta.parent.name)
    lone = [p.parent.name for p in sol.glob("*/*/sol.py")
            if not (p.parent / "meta.json").exists()]
    n = len(list(sol.glob("*/*/meta.json")))
    if bad or lone:
        return False, f"缺 sol.py：{bad[:5]}；缺 meta.json：{lone[:5]}"
    return True, f"{n} 题全部成对"


def probe_site(_a: dict) -> tuple[bool, str]:
    bad = []
    for no, m in sol_store.load_all().items():
        want = sol_store.site_of(no)
        got_dir = sol_store.meta_path(no).parent.parent.name
        if want != got_dir or m.get("site") not in (None, want):
            bad.append(f"{no}(目录 {got_dir} / 注册表 {want} / meta {m.get('site')})")
    if bad:
        return False, "、".join(bad[:5])
    return True, "逐题一致（目录层名 == 注册表 == meta.site）"


def probe_spj(_a: dict) -> tuple[bool, str]:
    metas = sol_store.load_all()
    has_file = {no for no in metas if sol_store.spj_path(no).exists()}
    declared = {no for no, m in metas.items()
                if (m.get("judge") or {}).get("mode") == "spj"}
    only_file = sorted(has_file - declared)
    only_decl = sorted(declared - has_file)
    ndrv = sum(1 for no in metas if sol_store.driver_path(no).exists())
    if only_file or only_decl:
        return False, f"有 spj.py 没声明：{only_file}；声明了没文件：{only_decl}"
    return True, f"{len(has_file)} 个 spj.py 双向对齐，另有 {ndrv} 个 driver.py"


def probe_redirects(_a: dict) -> tuple[bool, str]:
    """题解页 URL 一处没变，所以重定向表里不该有 `solutions/` 的条目。

    只在 `redirect_maps:` 那一段里数，别在整份 mkdocs.yml 上瞎找——
    nav 里也全是 `.md`，混进来这个数就没有出处了（教训十一）。
    """
    lines = (text("mkdocs.yml") or "").splitlines()
    try:
        start = next(i for i, ln in enumerate(lines) if ln.strip() == "redirect_maps:")
    except StopIteration:
        return False, "mkdocs.yml 里找不到 redirect_maps:"
    indent = len(lines[start]) - len(lines[start].lstrip())
    entries = []
    for ln in lines[start + 1:]:
        if ln.strip() and not ln.strip().startswith("#") and \
                len(ln) - len(ln.lstrip()) <= indent:
            break
        if re.search(r"\.md\"?\s*:", ln):
            entries.append(ln.strip())
    hit = [e for e in entries if "solutions/" in e]
    if hit:
        return False, f"重定向表里出现题解条目 {len(hit)} 条：{hit[:3]}"
    return True, f"重定向 {len(entries)} 条，无一条指向题解（URL 未变，零重定向成本）"


def _redirect_rows(lines: list) -> list:
    """从 mkdocs.yml 的 `redirect_maps:` 段里抽出 `旧: 新` 两列，注释与缩进都剥掉。"""
    try:
        start = next(i for i, ln in enumerate(lines) if ln.strip() == "redirect_maps:")
    except StopIteration:
        return []
    indent = len(lines[start]) - len(lines[start].lstrip())
    rows = []
    for ln in lines[start + 1:]:
        if ln.strip() and not ln.strip().startswith("#") and                 len(ln) - len(ln.lstrip()) <= indent:
            break
        m = re.match(r'\s*"?([^"#:]+\.md)"?\s*:\s*(\S+)\s*$', ln)
        if m:
            rows.append((m.group(1), m.group(2)))
    return rows


def probe_readme_markers(_a: dict) -> tuple[bool, str]:
    """README 里那几个「构建期同步的数」的标记，形态得是好的、数得是对的。

    两件事一起查：

    1. **没有被改坏的标记。** 写成 `<!--N:chapters-->`（尖括号里不留空格）时，
       markdown 格式化插件会把它当成自动链接，改写成
       `[!--N:chapters--](!--N:chapters--)`——**这一版真被推上过线**，
       GitHub 仓库首页上明晃晃印着 `!--N:chapters--`。改成带空格的形态就免疫了，
       但没人拦着谁再写回去。
    2. **标记里的数与实测一致。** 等价于「`gen_index.py` 跑过且没被回改」。

    这一条是 09 教训十八的又一个实例，但方向反过来：那一条讲「规则写了却不生效」，
    这一条讲**「产物看着对，渲染出来却不对」**——`git diff` 干净、脚本全绿，
    而 GitHub 页面上是坏的，因为**没有任何闸门看渲染结果**。

    **看不见的**：只查 README。站点那一侧的 `<!-- N:xxx -->` 由 hook 在构建期吃掉，
    渲染不出来就是空字符串，那一类要靠 build 之后数页面里的数字。
    """
    body = text("README.md")
    if body is None:
        return False, "README.md 不存在"

    broken = re.findall(r"\[!--\s*/?N[:\w]*\s*--\]", body)
    if broken:
        return False, (f"README 里有 {len(broken)} 处标记被改写成了 markdown 链接 "
                       f"{broken[:3]}——多半是编辑器的 markdown 格式化插件干的，"
                       f"标记要写成 `<!-- N:xxx -->`（尖括号里留空格）")

    pairs = re.findall(r"<!--\s*(N:\w+)\s*-->([^<]*)<!--\s*/N\s*-->", body)
    if not pairs:
        return False, "README 里一个 `<!-- N:xxx -->` 标记都没有——是被整段删掉了吗"

    want = {}
    mp = json.loads((ROOT / "data" / "_mapping.json").read_text(encoding="utf-8"))["chapters"]
    want["N:chapters"] = str(len(mp))
    probs = json.loads((ROOT / "data" / "_problems.json").read_text(encoding="utf-8"))
    want["N:problems"] = str(len(probs))
    vols: dict = {}
    for f in sorted((ROOT / "docs").rglob("*.md")):
        rel = f.relative_to(ROOT / "docs")
        if f.name == "index.md" or rel.parts[0] == "appendix":
            continue
        m = re.search(r"^volume:\s*(\d+)\s*$", f.read_text(encoding="utf-8"), re.M)
        if m:
            vols[m.group(1)] = vols.get(m.group(1), 0) + 1
    for v, n in vols.items():
        want["N:vol" + v] = str(n)

    stale = [(k, got, want.get(k)) for k, got in pairs
             if k in want and got.strip() != want[k]]
    unknown = sorted({k for k, _ in pairs if k not in want})
    if stale:
        return False, f"{len(stale)} 处标记的数过期了 {stale[:3]}——跑一次 gen_index.py"
    if unknown:
        return False, f"README 里有本探针不认识的标记 {unknown}——加了新标记就要在这里登记"
    return True, f"{len(pairs)} 处标记形态正常、数与实测一致"


def probe_py39_pinned(_a: dict) -> tuple[bool, str]:
    """「全书代码兼容 Python 3.9」这句承诺，得有人真的在那个版本上验。

    三处必须对得上：
    · `pyproject.toml` 的 `requires-python` 下界
    · `.github/workflows/deploy.yml` 里 `setup-python` 的版本（每个 job）
    · `scripts/check_syntax.py` 在 CI 里跑——它用**运行它的解释器**去 `ast.parse`，
      所以上一条是几，验的就是几

拦的是「有人把 CI 升到 3.12，承诺照旧写着 3.9，而闸门跟着升上去、
从此再也拦不住 3.10 语法」——规则还在，只是不再检查它声称检查的东西（09 教训十八）。

**看不见的**：只查语法版本对齐，不查运行时 API。`itertools.pairwise` 这类是
合法语法、导入才炸，靠 `verify.py` 真跑一遍才抓得到。
    """
    proj = text("pyproject.toml") or ""
    m = re.search(r'requires-python\s*=\s*"[><=~^]*\s*(\d+\.\d+)', proj)
    if not m:
        return False, "pyproject.toml 里读不到 requires-python"
    floor = m.group(1)

    wf = text(".github/workflows/deploy.yml") or ""
    vers = re.findall(r'python-version:\s*"?([\d.]+)"?', wf)
    if not vers:
        return False, "workflow 里读不到 python-version"
    bad = sorted({v for v in vers if v != floor})
    if bad:
        return False, (f"pyproject 下界 {floor}，而 workflow 里有 {bad}——"
                       f"CI 验的不是承诺的那个版本")

    if "scripts/check_syntax.py" not in wf:
        return False, "workflow 里没有跑 scripts/check_syntax.py，语法承诺没人验"
    return True, f"pyproject 下界与 {len(vers)} 处 CI 版本一致（{floor}），且 CI 跑 check_syntax"


def probe_volume_counts_agree(_a: dict) -> tuple[bool, str]:
    """两套「每卷多少章」的口径必须一致。

    · `hooks/build_pages.py` 的 `_walk_volumes()` 数 **nav 顶层分组**（站点首页用它）
    · `scripts/gen_index.py` 的 `volume_counts()` 数 **front-matter 的 `volume`**（README 用它）

    两者本该永远相等，所以谁都不会去比。而「本该相等却没人比」正是分叉的温床：
    往 nav 里挪一章却忘了改 front-matter，站点与 README 会各说各话，两边都不报错。
    这一条把**分歧本身**当成指标（09 教训二十六）。

    **看不见的**：它只比每卷的**章数**，不比是哪几章。两处各挪走一章又换进来一章，
    数对得上而归属错了——那一类要靠 `nav ↔ 磁盘 ↔ _mapping` 的四向差集。
    """
    nav: dict = {}
    order = []
    in_nav = False
    cur = None
    for line in (text("mkdocs.yml") or "").splitlines():
        if line.rstrip() == "nav:":
            in_nav = True
            continue
        if not in_nav:
            continue
        m = re.match(r"^  - (\S.*):\s*$", line)          # 顶层分组
        if m:
            cur = m.group(1)
            if cur not in nav:
                nav[cur] = 0
                order.append(cur)
            continue
        m = re.match(r"^\s+- .*:\s*(\S+\.md)\s*$", line)
        if m and cur and "/" in m.group(1) and not m.group(1).endswith("/index.md") \
                and not m.group(1).startswith(("solutions/", "appendix/")):
            nav[cur] += 1
    nav_counts = [n for t_, n in ((k, nav[k]) for k in order) if n]

    fm: dict = {}
    for f in sorted((ROOT / "docs").rglob("*.md")):
        rel = f.relative_to(ROOT / "docs")
        if f.name == "index.md" or rel.parts[0] == "appendix":
            continue
        m = re.search(r"^volume:\s*(\d+)\s*$", f.read_text(encoding="utf-8"), re.M)
        if m:
            fm[m.group(1)] = fm.get(m.group(1), 0) + 1
    fm_counts = [fm[k] for k in sorted(fm)]

    if nav_counts != fm_counts:
        return False, (f"两套口径分叉：nav 顶层分组 {nav_counts}，"
                       f"front-matter volume {fm_counts}")
    return True, f"nav 与 front-matter 一致，每卷 {fm_counts}（合计 {sum(fm_counts)}）"


def probe_examples_generated(_a: dict) -> tuple[bool, str]:
    """章首例题块**只许生成，不许手写**（04 §四 细节 3，用户 2026-08-25 拍板形态）。

    两个方向各一条：
    ① `docs/` 里一处手写的 `> **配套例题**：…` 都不许剩——它是 P1② 攒下来的债，
       P-R① 原子④ 清完，往后再出现就是有人把生成的换回手写（09 教训七）；
    ② 挂了例题的章，`<!-- CHAPTER-EXAMPLES -->` 一个都不许少。表 token 不在这里管，
       它允许有窗口期（`check_orphan` 的计数器盯着），而章首那一句是每章第一屏。

    **看不见的**：它只问 token 在不在，不问渲染出来对不对——
    那一条靠 `mkdocs build` 之后数页面里「本章配套 N 道例题」的出现次数。
    """
    docs = ROOT / "docs"
    mapping = json.loads((DATA / "_mapping.json")
                         .read_text(encoding="utf-8"))["chapters"]
    hand, miss = [], []
    for md in sorted(docs.rglob("*.md")):
        body = md.read_text(encoding="utf-8")
        if re.search(r"^\s*>?\s*\*\*配套例题\*\*", body, re.M):
            hand.append(md.relative_to(docs).as_posix())
    for cid, probs in sorted(mapping.items()):
        f = docs / (cid + ".md")
        if probs and f.is_file() and "<!-- CHAPTER-EXAMPLES -->" not in f.read_text(encoding="utf-8"):
            miss.append(cid)
    if hand or miss:
        return False, (f"手写「配套例题」残留 {len(hand)} 处 {hand[:3]}；"
                       f"有例题却缺章首 token 的章 {len(miss)} 个 {miss[:3]}")
    n = sum(1 for c, v in mapping.items() if v)
    return True, f"手写残留 0 处；{n} 个有例题的章章首 token 全在"


def probe_io_pointer(_a: dict) -> tuple[bool, str]:
    """入门段用了快读的章，必须有一处把读者指向 `toolkit/io.md`（`R2-14-5`）。

    读者的原话是「入门段自己就铺满了快读，对初次学习反而是负担」。量化依据：
    讲这套写法的正主 `toolkit/io.md` 是 **20 章**，排在 `python/` 全部 16 章之后，
    而 `python/` 里 13 个文件在它之前就用上了 `sys.stdin.buffer.read()`。

    **判据是「有没有指路」，不是「用不用快读」**（`Q23-3`）。逐处过完 36 个位置，
    没有一处属于「讲算法本身的教学片段」——要么是例题的完整题解（必须能过判题机），
    要么本身就在讲 I/O。所以要还的债是指引，不是把代码降档。

    **看不见的**：它只问链接在不在，不问它离那段代码有多远，也不问措辞对不对。
    这两样没有闸门，靠写作纪律（09 教训四）。
    """
    d = ROOT / "docs" / "python"
    miss = [p.name for p in sorted(d.glob("*.md"))
            if "buffer.read" in (b := p.read_text(encoding="utf-8"))
            and "toolkit/io.md" not in b]
    n = sum(1 for p in d.glob("*.md") if "buffer.read" in p.read_text(encoding="utf-8"))
    if miss:
        return False, f"python/ 下 {len(miss)} 个文件用了快读却没有指路：{miss}"
    return True, f"python/ 下用快读的 {n} 个文件各有一处指向 toolkit/io.md"


def probe_reports_fresh(_a: dict) -> tuple[bool, str]:
    """闸门报告本身会过期，而**只有 `check_prose` 会喊自己过期**。

    `P-N②` 锁定复核实测：`dev/audit/模板代码盘点.md` 写着 Python 顶格代码块
    **1092** 段，而现算是 **1108**——落后 16 段，跨了四个批次没人发现。
    `check_prose` 有 `overview_stale()`，跑一次就会打印 `[过期]`；
    其余八个闸门的报告**没有任何过期检测**，只有重新生成才会暴露。

    这里按教训二十六办：**两个判据指向同一个对象时，把「它们不一致」也当成一个指标**。
    `check_templates` 与 `check_prose.code_stats()` 数的是同一件事
    （顶格 ` ```python ` 块），拿报告里落盘的那个数与现算比一次即可。

    **看不见的**：只盯这一个数。报告里别的段落过期了照样看不出来——
    真正的解法是收尾时把生成脚本全部重跑一遍（`08 §2.3` 第 4 步）。
    """
    rel = "dev/audit/模板代码盘点.md"
    body = text(rel)
    if body is None:
        return False, f"报告不存在：{rel}　→ 跑一次 scripts/check_templates.py"
    m = re.search(r"^\|\s*Python\s*\|\s*(\d+)\s*\|", body, re.M)
    if not m:
        return False, f"{rel} 里找不到「Python | 顶格代码块」那一行，格式变了"
    sys.path.insert(0, str(ROOT / "scripts"))
    import check_prose
    now = check_prose.code_stats()["total"]
    was = int(m.group(1))
    if was != now:
        return False, (f"{rel} 过期：写着 Python {was} 段，现算 {now} 段"
                       f"　→ 跑一次 scripts/check_templates.py")
    return True, f"模板盘点报告与现算一致（Python 顶格代码块 {now} 段）"


def probe_redirects_sync(_a: dict) -> tuple[bool, str]:
    """`dev/_redirects.yml` 与 `mkdocs.yml` 的 `redirect_maps` 必须逐行一致。

    两份文件的头注释**声称**它们一致（「内容与 mkdocs.yml 的
    plugins.redirects.redirect_maps 逐行一致」），但在 P-R① 之前没有任何一处校验它——
    正是 09 教训十八说的「长得像生效的规则」：读起来完全正常，真跑起来才知道。
    生效的只有 mkdocs.yml 那一份，`dev/_redirects.yml` 是清单与线上验收的依据，
    两边分叉时线上验收会照着一份过期清单逐条请求，全绿而漏检。
    """
    yml = text("dev/_redirects.yml")
    if yml is None:
        return False, "dev/_redirects.yml 不存在"
    listed = []
    for ln in yml.splitlines():
        m = re.match(r"\s*([^#:]+\.md)\s*:\s*(\S+)\s*$", ln)
        if m:
            listed.append((m.group(1), m.group(2)))
    live = _redirect_rows((text("mkdocs.yml") or "").splitlines())
    if not live:
        return False, "mkdocs.yml 里找不到 redirect_maps:"
    only_yml = sorted(set(listed) - set(live))
    only_yml_ = sorted(set(live) - set(listed))
    if only_yml or only_yml_:
        return False, (f"两份重定向表分叉：只在 _redirects.yml 的 {len(only_yml)} 条 "
                       f"{only_yml[:2]}；只在 mkdocs.yml 的 {len(only_yml_)} 条 {only_yml_[:2]}")
    return True, f"两份重定向表逐行一致，共 {len(live)} 条"


def _count(kind: str) -> int:
    metas = sol_store.load_all()
    if kind == "judge":
        return len(sol_store.judge_cfg(metas))
    if kind == "submitlang":
        return len(sol_store.submit_langs(metas))
    return len(sol_store.submit_results(metas))


def probe_judge_count(a: dict) -> tuple[bool, str]:
    n = _count("judge")
    return n == a["expect"], f"{n} 题带判题配置（预期 {a['expect']}）"


def probe_submitlang_count(a: dict) -> tuple[bool, str]:
    n = _count("submitlang")
    return n == a["expect"], f"{n} 题登记了提交语言（预期 {a['expect']}）"


def probe_result_count(a: dict) -> tuple[bool, str]:
    n = _count("result")
    return n == a["expect"], f"{n} 题有提交判定（预期 {a['expect']}）"


def probe_verify_state(_a: dict) -> tuple[bool, str]:
    """键必须是题号。以文件名 / path.stem 为键的状态文件会在改名批次里塌掉。"""
    p = ROOT / "solutions" / "_verify_state.json"
    if not p.is_file():
        return False, "solutions/_verify_state.json 不存在"
    d = json.loads(p.read_text(encoding="utf-8"))
    known = set(sol_store.all_numbers())
    bad = sorted(k for k in d if k not in known)
    if bad:
        return False, f"{len(bad)} 个键不是磁盘上的题号：{bad[:5]}"
    return True, f"{len(d)} 条，键全部是题号"


def probe_topics(_a: dict) -> tuple[bool, str]:
    ch = mapping()
    want: dict = {}
    for c, qs in ch.items():
        for q in qs:
            want.setdefault(q, []).append(c)
    bad = []
    for no, m in sol_store.load_all().items():
        if sorted(m.get("topics") or []) != sorted(want.get(no, [])):
            bad.append(no)
    if bad:
        return False, f"{len(bad)} 题与 _mapping 反查不一致：{bad[:5]}（改完归属要跑 migrate_solutions.py --sync）"
    return True, "逐题一致"


def probe_topics_split(a: dict) -> tuple[bool, str]:
    """有归属 / 无归属两档的题数。**上界是棘轮，不是快照。**

    原判据写死 `[165, 201]`——那是 P-M③ 当天的现状，而「把 201 道孤儿题归属掉」
    正是排期里的既定工作，断言等于在拦它要拦的那件事（教训七：派生数字不要手写）。
    改成两条各自说得清边界的：

    * `total` **锁死**：磁盘题数必须恰好是它。少一题就是题目丢了，多一题就是
      有题没进注册表——两种都是真问题，与归属进度无关。
    * `max_miss` **只许降**：未归属数是欠账，棘轮上界跟着 `check_prose` 的同一套办法
      （教训十四）。归属做完一批就把上界压到实测值，**压之前先确认没有超出**。
      它拦得住的是「某次 `--sync` 或改表把已归属的题打回未归属」。
    """
    metas = sol_store.load_all()
    hit = sum(1 for m in metas.values() if m.get("topics"))
    miss = len(metas) - hit
    exp = a["expect"]
    total, cap = exp["total"], exp["max_miss"]
    msg = f"有归属 {hit} / 无归属 {miss}（题数应为 {total}，未归属上界 {cap}）"
    if hit + miss != total:
        return False, msg
    return miss <= cap, msg


_STR = re.compile(r'"""(?:.|\n)*?"""|\'\'\'(?:.|\n)*?\'\'\'|"[^"\n]*"|\'[^\'\n]*\'')
_COMMENT = re.compile(r"#.*$", re.M)
_FLAT = re.compile(r"solutions\s*/\s*['\"]?\s*\+|SOL\s*/\s*f?['\"]\{?no")


def probe_problem_count_consistent(_a: dict) -> tuple[bool, str]:
    """首页、README、附录 A 的题数必须一致（05 §P1 验收门槛的最后一条）。

    **这条门槛写在方案里，五个批次里没有任何一批核过它**——其余七条都有闸门，
    只有它没有，于是它被勾选而不是被执行（09 教训二十七）。
    P1 阶段复核实测：首页当时写 165、另两处写 366，**整个 P1 阶段都不满足**。
    （165 复现得出来：BISHI 147 ＋ PIO 18，是 P-M③ 之前的口径。）

    三处现在都是生成的——首页走 `hooks/build_pages.py` 的 `<!-- N:problems -->`、
    README 与附录 A 走 `gen_index.py`——所以这条断言拦的是**生成器之间打架**，
    以及有人把某一处改回手写。数的是 `_problems.json` 的题数这个唯一权威。
    """
    total = len(json.loads((DATA / "_problems.json").read_text(encoding="utf-8")))
    bad = []

    # 首页数的不是「有没有 token」而是「有没有写死的数」——**反向验证时实测出来的**：
    # 首页有两处 <!-- N:problems -->，只改坏一处时「有 token」这个判据照样绿。
    home = text("docs/index.md") or ""
    hard = re.findall(r"(\d+)\s*(?:道真题|道题一张表|章正文|个部分|题通过判题机)", home)
    if hard:
        bad.append(f"首页有写死的数 {hard}（应为构建期注入的 <!-- N:… -->）")
    if "<!-- N:problems -->" not in home:
        bad.append("首页缺 <!-- N:problems --> 注入点")

    ap = text("docs/appendix/a-problems.md") or ""
    m = re.search(r"共\s*(\d+)\s*题", ap)
    if not m or int(m.group(1)) != total:
        bad.append(f"附录 A 写 {m.group(1) if m else '?'}")
    rows = len(re.findall(r"^\| \[[A-Z]+\d+\]", ap, re.M))
    if rows != total:
        bad.append(f"附录 A 表格 {rows} 行")

    rd = text("README.md") or ""
    m = re.search(r"题解：\*\*(\d+)\s*/\s*(\d+)\s*已写", rd)
    if not m or int(m.group(2)) != total:
        bad.append(f"README 写 {m.group(2) if m else '?'}")

    return (not bad), (f"三处一致，均为 {total} 题" if not bad
                       else f"权威 {total}；" + "、".join(bad))


def probe_problem_links(a: dict) -> tuple[bool, str]:
    """每道已归属的题，在它 `_mapping.json` 所挂的那一章里至少有一条通往题解页的链接。

    P1③b 的第一摊（08 §6.3 第 29 条）：正文里的裸题号点不进已经写好的题解页，
    是发布出去的版本最实的破绽。

    判据分两半（教训二十三：不变量归不变量、现状归棘轮）：

    | 半 | 写法 | 拦什么 |
    | --- | --- | --- |
    | `strict` 里的前缀 | **一道都不许缺** | 本批清干净的那一档（BM / LC）往后不许回潮 |
    | 其余前缀 | `max_miss` **只许降** | BISHI 那 21 道老账（08 §6.3 第 32 条，归 P6） |

    数的是**链接目标**（`](…/solutions/<题号>.md)`）不是链接文字：
    BISHI 那 148 处写的是 ``[`solutions/nowcoder/BISHI64/sol.py`](../solutions/BISHI64.md)``，
    链接文字是仓库物理路径（08 §6.3 第 22 条那一摊，归 P6 统一定夺）。
    读者点得进去这件事，与链接文字长什么样是两码事，这条断言只管前者。
    """
    import collections
    mapping = json.loads((DATA / "_mapping.json").read_text(encoding="utf-8"))["chapters"]
    prob2ch: dict = {}
    for ch, ps in mapping.items():
        for pr in ps:
            prob2ch.setdefault(pr, set()).add(ch)
    pat = re.compile(r"\]\((?:\.\./)*solutions/([A-Z]+\d+)\.md[)#]")
    linked = collections.defaultdict(set)
    docs = ROOT / "docs"
    for f in docs.rglob("*.md"):
        rel = f.relative_to(docs).as_posix()
        if rel.startswith(("appendix/", "solutions/")):
            continue
        for m in pat.finditer(f.read_text(encoding="utf-8")):
            linked[m.group(1)].add(rel[:-3])
    miss = sorted(no for no, chs in prob2ch.items() if not (linked[no] & chs))
    strict = tuple(a.get("strict") or ())
    hard = [no for no in miss if no.startswith(strict)]
    soft = [no for no in miss if not no.startswith(strict)]
    ok = not hard and len(soft) <= a["max_miss"]
    msg = (f"{len(prob2ch) - len(miss)} / {len(prob2ch)} 道已归属的题在本章有题解链接；"
           f"{'/'.join(strict)} 缺 {len(hard)}（须为 0）、其余缺 {len(soft)}（上界 {a['max_miss']}）")
    if hard:
        msg += "　—— " + "、".join(hard[:8])
    return ok, msg


def probe_anchors_registered(a: dict) -> tuple[bool, str]:
    """`_source_topics.json` 里「还没登记 anchors」的条目数——**棘轮，只许降**。

    这是现状不是不变量（教训二十三），所以写成带方向的上界：P1③b 把它从 160 压到 0，
    往后新增知识点条目时允许暂时空着，但不许把已经登记的 anchors 删回去。
    数的是「既没 anchors 也没 excluded」的条目。
    """
    d = json.loads((DEV_DATA / "_source_topics.json").read_text(encoding="utf-8"))
    n = sum(1 for g, items in d.items() if not g.startswith("_")
            for _, v in items.items() if not v.get("excluded") and not v.get("anchors"))
    return n <= a["max"], f"未登记 anchors {n} 条（上界 {a['max']}）"


def probe_prose_ratchet(a: dict) -> tuple[bool, str]:
    """章骨架三条（S1 / S2 / S4）的棘轮基线必须是 0，SC3 恰好是它的定值。

    `check_prose` 自己只拦「超出基线」，**拦不住有人回头再跑一次 `--baseline`
    把回潮写成新基线**——那一步会静悄悄地把单向门变回可调阀门。这条断言看的是
    基线文件本身，所以它拦得住的正是「改基线」这个动作（教训十四 / 二十三）。

    SC3 写成**定值**而不是上界：那 4 处是逐个看过的收束语（08 §6.3 第 10 条），
    往后只要求不新增；真要减，改这里的期望值时会被逼着说清减掉的是哪一处。
    """
    import json as _json
    f = DATA / "_prose_baseline.json"
    if not f.is_file():
        return False, "找不到 data/_prose_baseline.json"
    counts = _json.loads(f.read_text(encoding="utf-8")).get("counts", {})
    tot = {r: sum(counts.get(r, {}).values()) for r in a["expect"]}
    bad = {r: n for r, n in tot.items() if n != a["expect"][r]}
    msg = "、".join(f"{r} {n}" for r, n in sorted(tot.items()))
    return (not bad), msg + ("" if not bad else f"　期望 {a['expect']}")


def probe_no_flat_path(_a: dict) -> tuple[bool, str]:
    """消费方不许自己拼 `solutions/<题号>.py`。查的是代码，不是注释与文案。"""
    bad = []
    for p in sorted((ROOT / "scripts").glob("*.py")) + [ROOT / "hooks" / "build_pages.py"]:
        if p.name in ("sol_store.py", "migrate_solutions.py", "check_decisions.py"):
            continue          # 查表层自己 + 迁移脚本 + 本脚本
        code = _COMMENT.sub("", _STR.sub('""', p.read_text(encoding="utf-8")))
        if _FLAT.search(code):
            bad.append(p.name)
    if bad:
        return False, f"仍自己拼路径：{bad}"
    return True, "剥掉注释与字符串后无一处自拼扁平路径"


def probe_prose_stdlib_only(_a: dict) -> tuple[bool, str]:
    """CI 只 `pip install mkdocs-material mkdocs-redirects`，没有 uv、没有别的包。

    连 import 链一起查：`check_prose` 会 import `verify_docs`，`verify_docs`
    再 import `sol_store`——链上任何一环引了第三方包，CI 都会在那一步炸。

    判据是「模块的 origin 落在标准库目录里」，不是一张写死的白名单：
    白名单会随 Python 版本过期，而这条判据在哪个版本上都成立。
    """
    import importlib.util
    import sysconfig

    stdlib_dir = Path(sysconfig.get_paths()["stdlib"]).resolve()
    local = {q.stem for q in (ROOT / "scripts").glob("*.py")}
    bad = []
    for name in ("check_prose", "verify_docs", "sol_store"):
        code = (ROOT / "scripts" / f"{name}.py").read_text(encoding="utf-8")
        for m in re.finditer(r"^\s*(?:from|import)\s+([A-Za-z_][\w.]*)", code, re.M):
            top = m.group(1).split(".")[0]
            if top in local or top == "__future__":
                continue
            try:
                spec = importlib.util.find_spec(top)
            except (ImportError, ValueError):
                spec = None
            if spec is None:
                bad.append(f"{name} -> {top}（找不到）")
                continue
            if spec.origin in (None, "built-in", "frozen"):
                continue
            try:
                Path(spec.origin).resolve().relative_to(stdlib_dir)
            except ValueError:
                bad.append(f"{name} -> {top}")
    if bad:
        return False, "引了标准库之外的包：" + "、".join(sorted(set(bad)))
    return True, "check_prose / verify_docs / sol_store 三份只 import 标准库"


def probe_orphan_full_scope(_a: dict) -> tuple[bool, str]:
    """孤儿核对的分母必须是磁盘上的全部题，不是 `_mapping` 里的那一部分。"""
    rep = ROOT / "dev" / "audit" / "孤儿题核对.md"
    if not rep.is_file():
        return False, "还没跑过 check_orphan.py"
    m = re.search(r"磁盘 \*\*(\d+)\*\* 题", rep.read_text(encoding="utf-8"))
    n = len(sol_store.all_numbers())
    if not m:
        return False, "报告里读不到题数"
    return int(m.group(1)) == n, f"报告 {m.group(1)} 题 / 磁盘 {n} 题"


def probe_cpp_judged(_a: dict) -> tuple[bool, str]:
    """决议 M：201 道 core 题的 C++ 轨要有判题机判定。落地在 P2。"""
    metas = sol_store.load_all()
    core = [no for no, m in metas.items() if m.get("mode") == "core"]
    done = [no for no in core
            if ((metas[no].get("langs") or {}).get("cpp") or {}).get("status")]
    return len(done) == len(core), f"core {len(core)} 题，C++ 有判定 {len(done)} 题"


def probe_cpp_track_pages(_a: dict) -> tuple[bool, str]:
    """决议 N：C++ 附轨页 `<slug>.cpp.md`。落地在 P2（卷一）/ P4（卷二）。"""
    n = len(list(DOCS.rglob("*.cpp.md")))
    return n > 0, f"附轨页 {n} 个"


def probe_cpp_track_not_counted(_a: dict) -> tuple[bool, str]:
    """决议 N 的硬约束：附轨页**不是独立章**——nav 不单列、`_mapping.json` 不加键。

    这一条现在「通过」只是因为附轨页一个都还没有。P2 铺开附轨的那一批要重跑它，
    那时它才真正开始起作用。
    """
    pages = {p.relative_to(DOCS).as_posix()[:-3] for p in DOCS.rglob("*.cpp.md")}
    if not pages:
        return True, "还没有附轨页，本条暂时空跑（P2 铺开后才真正起作用）"
    chapters = set(mapping())
    nav = text("mkdocs.yml") or ""
    bad = [q for q in pages if q in chapters or f"{q}.md" in nav]
    if bad:
        return False, f"附轨页混进了 nav / _mapping：{bad[:5]}"
    return True, f"{len(pages)} 个附轨页都没混进 nav / _mapping"


def _topics_json() -> dict:
    import json as _json
    f = DEV_DATA / "_topics.json"
    if not f.is_file():
        return {}
    return {k: v for k, v in _json.loads(f.read_text(encoding="utf-8")).items()
            if not k.startswith("_")}


def probe_topics_shape(_a: dict) -> tuple[bool, str]:
    """_topics.json 每条都要有档、依据、依据类型、关键词，且 ref/out 不挂章。

    「写不出依据的条目说明它本身没想清楚」（07 §3.1）——这条把它变成断言。
    """
    reg = _topics_json()
    if not reg:
        return False, "dev/data/_topics.json 不存在或为空（P0c 的产出）"
    bad = []
    for k, v in reg.items():
        miss = [f for f in ("inclusion", "evidence", "basis", "aliases") if not v.get(f)]
        if miss:
            bad.append(f"{k} 缺 {'/'.join(miss)}")
        elif v["inclusion"] not in ("core", "ext", "ref", "out"):
            bad.append(f"{k} 非法档 {v['inclusion']}")
        elif v["inclusion"] in ("ref", "out") and (v.get("chapters") or v.get("planned")):
            bad.append(f"{k} 是 {v['inclusion']} 档却挂了章")
        elif v["inclusion"] in ("core", "ext") and not v.get("chapters") and not v.get("planned"):
            bad.append(f"{k} 是 {v['inclusion']} 档却一章未挂")
    if bad:
        return False, f"{len(bad)} 条不合形状：{bad[:3]}"
    return True, f"{len(reg)} 条形状齐备"


def probe_topics_basis_consistent(_a: dict) -> tuple[bool, str]:
    """`basis` 与其余字段自洽——P0c 锁定复核加的（当时报出 12 条）。

    `topics_shape` 只看「字段齐不齐」、`topics_core_basis` 只看 core 的两条必要条件，
    **中间这段没人看**：依据类型之间、依据与字段之间的矛盾。实测漏出四类：

    | 规则 | 依据 | 锁定复核时的实例 |
    | --- | --- | --- |
    | 有 `planned` ⇒ 记 `plan-listed` | `planned` 的定义就是「02 §5 清单里的目标章」 | 7 条（虚树、树上启发式合并、上下界网络流……） |
    | `rare-in-oi` ⇒ 零命中 且 无 `plan-listed` | 该依据的定义是「零覆盖 ＋ 无模板题 ＋ 02 §5 未列」 | 3 条（块状链表、拟阵、Slope Trick） |
    | `prose-zero` 与 `prose-covered` 互斥 | 一条正文不可能既 0 命中又有命中 | 0 条（但零成本） |
    | `luogu-template` ⇒ evidence 写得出题号 | 07 §3.1「题号写进 evidence」 | 0 条（②③ 一直照做） |

    **07 §3 分档示例点名过的条目走 `rare-in-oi` 的「或」分支**（见 `_schema.basis_types`），
    所以那几条豁免第二行的前半句。
    """
    reg = _topics_json()
    if not reg:
        return False, "dev/data/_topics.json 不存在（P0c 的产出）"
    # 07 §3 分档示例点名为 ref/ext 的条目：rare-in-oi 走「或」分支
    NAMED = ("PQ 树", "手指树", "AA 树", "析合树", "Jordan", "环论", "域论",
             "Meissel", "洲阁筛", "希尔排序", "锦标赛排序",
             "笛卡尔树", "珂朵莉树", "后缀树", "稳定匹配")
    bad = []
    for k, v in reg.items():
        b = set(v.get("basis") or [])
        named = any(x in k for x in NAMED)
        if v.get("planned") and "plan-listed" not in b:
            bad.append(f"{k} 有 planned 却没记 plan-listed")
        if "rare-in-oi" in b and "plan-listed" in b and not named:
            bad.append(f"{k} 同时记了 rare-in-oi 与 plan-listed")
        if "rare-in-oi" in b and "prose-covered" in b and not named:
            bad.append(f"{k} 同时记了 rare-in-oi 与 prose-covered")
        if {"prose-zero", "prose-covered"} <= b:
            bad.append(f"{k} 同时记了 prose-zero 与 prose-covered")
        if "luogu-template" in b and not re.search(r"[PB]\d{4,5}|【模板】", v.get("evidence", "")):
            bad.append(f"{k} 记了 luogu-template 但 evidence 没写题号")
    if bad:
        return False, f"{len(bad)} 条依据不自洽：{bad[:3]}"
    return True, f"{len(reg)} 条依据自洽"


def probe_topics_core_basis(_a: dict) -> tuple[bool, str]:
    """core 的两条必要条件（_topics.json 的 _schema.core_判据）。

    ①章清单容得下它（has-chapter / plan-listed）②另有一条独立依据。
    07 §3.1 末句「没有依据的条目一律先记 ext，不记 core」——这条把它变成断言。
    """
    reg = _topics_json()
    if not reg:
        return False, "dev/data/_topics.json 不存在（P0c 的产出）"
    room = {"has-chapter", "plan-listed"}
    indep = {"luogu-template", "prose-covered", "repo-problem", "track-required"}
    bad = []
    for k, v in reg.items():
        if v.get("inclusion") != "core":
            continue
        b = set(v.get("basis") or [])
        if not (room & b):
            bad.append(f"{k} 无章可容")
        elif not (indep & b):
            bad.append(f"{k} 无独立依据")
    n = sum(1 for v in reg.values() if v.get("inclusion") == "core")
    if bad:
        return False, f"{len(bad)}/{n} 条 core 依据不足：{bad[:3]}"
    return True, f"core {n} 条依据齐备"


def probe_lessons_indexed(_a: dict) -> tuple[bool, str]:
    """09 里的每条教训，都要能从 08 §5 的速查表检索到。

    速查表是入口——只加 09 的正文而不加速查表那一行，下个窗口就找不到它，
    等于没加（08 §2.3 第 8 步）。这里查的是「每条教训至少被速查表点名一次」。
    """
    nine = text("dev/plan/09-已踩过的坑.md")
    eight = text("dev/plan/08-开工指引.md")
    if not nine:
        return False, "dev/plan/09-已踩过的坑.md 不存在"
    nums = re.findall(r"^### 教训([一二三四五六七八九十]+)：", nine, re.M)
    if not nums:
        return False, "09 里一条教训都没解析出来"
    if len(set(nums)) != len(nums):
        dup = [n for n in set(nums) if nums.count(n) > 1]
        return False, f"教训编号重复：{dup}（编号是永久标识，不许复用）"
    # 速查表在 08 的第五章里，取到下一个 ## 为止
    i = eight.find("## 五、已踩过的坑")
    j = eight.find("\n## ", i + 1)
    table = eight[i:j if j > 0 else len(eight)]
    miss = [n for n in nums if n not in table]
    if miss:
        return False, (f"{len(miss)} 条教训没进 08 §5 的速查表：教训"
                       + "、教训".join(miss) + "（加了正文没加索引 = 检索不到）")
    return True, f"{len(nums)} 条教训都能从速查表检索到"


def _ch5_rows() -> list:
    """解析 02 §5 那张表：`[(目录, 迁移后, 新增, 新增要点里的章 id 集合)]`。

    「新增要点」列里 `number/{mobius,du}` 这种花括号要展开成
    `math/number/mobius` / `math/number/du`，否则提前落地的章匹配不上。
    """
    doc = (ROOT / "dev/plan/02-结构与目录重构.md").read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r"^\| `([a-z]+)/` \| (\d+) \| \*{0,2}(\d+)\*{0,2} \| \d+ \| (.*) \|$",
                         doc, re.M):
        top, mig, add, cell = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
        ids = set()
        for part in re.split(r"[·、,，]", re.sub(r"（[^）]*）", "", cell)):
            part = part.strip().strip("`*").strip()
            if not part or " " in part.replace("/", " ").replace("{", " ") and "{" not in part:
                pass
            b = re.match(r"^([a-z0-9-]+)/\{([^}]*)\}$", part)
            if b:
                for leaf in b.group(2).split(","):
                    leaf = leaf.strip()
                    if leaf:
                        ids.add("%s/%s/%s" % (top, b.group(1), leaf))
                continue
            if re.fullmatch(r"[a-z0-9-]+(/[a-z0-9-]+)*", part):
                ids.add("%s/%s" % (top, part))
        out.append((top, mig, add, ids))
    return out


def probe_ch5_table(_a: dict) -> tuple[bool, str]:
    """02 §5 那张表的两列必须和磁盘对得上——**这是「天花板」这个数的地基**。

    表里「迁移后」是 P-M② 收尾那一刻的快照（74 ＋ 13 拆分 = 87），
    **不是「现在磁盘上有多少」**（89）。差的 2 章
    （`basic/divide-conquer` 决议 K、`dp/dag` 决议 E）是新增章提前落地，
    在「新增」列里已经算过，不重复计数。

    问题是**表上没有一个字说这件事**：谁拿「迁移后 87」去比磁盘 89，
    都会得出「02 过期了」（09 教训十的形状——「陈述事实但不声明状态」的格子）。
    光加注释治不了，注释也会过期，所以在这里把不变式写死：

        迁移后列之和  ＋  「新增要点」里已经落在磁盘上的章数  ==  磁盘章数

    **第一版写成了恒真式**（把「提前落地数」定义成差额本身，两边必然相等，
    09 教训十八的形状）。现在数的是**「新增要点」列里点名、且磁盘上确实有**的那些——
    于是三种走样都会当场变红：
      · 新开一章而两列都没登记；
      · 拆章之后忘了改「迁移后」列；
      · 提前落地的章从「新增要点」里被误删。
    """
    docs = ROOT / "docs"
    on_disk: dict = {}
    for f in docs.rglob("*.md"):
        rel = f.relative_to(docs)
        # **`.cpp.md` 附轨页不算章**（决议 N 的硬约束：nav 不单列、章数统计不计入）。
        # 不排除的话，P2 铺开 36 页附轨的当天本探针就会红——而且是**为了错误的理由**红：
        # 磁盘侧凭空多 36，表侧纹丝不动。今天附轨页 0 个，这条排除是提前铺的
        # （和 `check_prose.py` 里 S5 的 `exempt=[".cpp.md"]` 同一个理由）。
        if f.name == "index.md" or rel.parts[0] == "appendix" or f.name.endswith(".cpp.md"):
            continue
        on_disk.setdefault(rel.parts[0], set()).add(rel.as_posix()[:-3])

    rows = [r for r in _ch5_rows() if r[0] != "appendix"]
    if not rows:
        return False, "02 §5 的表没解析到——表格式变了，先改本探针"

    tab = landed = 0
    bad = []
    for top, mig, _add, planned in rows:
        have = on_disk.get(top, set())
        tab += mig
        hit = planned & have
        landed += len(hit)
        if len(have) != mig + len(hit):
            bad.append("%s/：迁移后 %d ＋ 已落地新增 %d ≠ 磁盘 %d"
                       % (top, mig, len(hit), len(have)))
    if bad:
        return False, "；".join(bad)
    total = sum(len(v) for v in on_disk.values())
    return True, ("迁移后 %d ＋「新增要点」里已落地的 %d = 磁盘 %d，逐目录都对得上"
                  % (tab, landed, total))


def probe_dup_same_chapter(_a: dict) -> tuple[bool, str]:
    """两套题单的重题（同一道题两个题号）必须挂在同一章。

    03 §3.3 第 4 条：「重题合并为一个条目，**正文只讲一次**，两站各自提交。」
    只讲一次的前提是两个题号落在同一章——分到两章去，那句承诺就自动失效了，
    而且没有任何别的闸门看得见（`check_orphan` 只问「有没有被引用」）。

    重题清单**不在这里重算**：`audit_newsets.norm_title()` 是唯一实现（教训十二：
    第二份实现迟早和第一份打架）。只对**两边都已归属**的对做断言——
    归属是分批推进的，一边有一边没有属于正常中间态。
    """
    import audit_newsets as ans

    d = json.loads((DATA / "_sources.json").read_text(encoding="utf-8"))
    sets_ = {x["key"]: x for x in d["sets"] if (ROOT / x["list"]).exists()}
    if not {"bm", "hot100"} <= set(sets_):
        return True, "两套新题单里至少一套不在册，本条不适用"

    a = json.loads((ROOT / sets_["bm"]["list"]).read_text(encoding="utf-8"))
    b = json.loads((ROOT / sets_["hot100"]["list"]).read_text(encoding="utf-8"))
    idx: dict = {}
    for it in a:
        idx.setdefault(ans.norm_title(it["title"]), []).append(it["no"])

    metas = sol_store.load_all()
    pairs, checked, bad = 0, 0, []
    for it in b:
        for x in idx.get(ans.norm_title(it["title"]), []):
            pairs += 1
            tx = sorted(metas.get(x, {}).get("topics") or [])
            ty = sorted(metas.get(it["no"], {}).get("topics") or [])
            if not tx or not ty:
                continue                      # 还没轮到，不是错
            checked += 1
            if tx != ty:
                bad.append(f"{x}{tx} ≠ {it['no']}{ty}")
    if bad:
        return False, f"{len(bad)} 对重题挂在不同章：{'；'.join(bad[:3])}"
    return True, f"重题 {pairs} 对，两边都已归属的 {checked} 对全部同章"


PROBES = {
    "cpp_judged": probe_cpp_judged,
    "cpp_track_pages": probe_cpp_track_pages,
    "cpp_track_not_counted": probe_cpp_track_not_counted,
    "prose_stdlib_only": probe_prose_stdlib_only,
    "orphan_full_scope": probe_orphan_full_scope,
    "layout": probe_layout, "pair": probe_pair, "site": probe_site, "spj": probe_spj,
    "redirects": probe_redirects, "redirects_sync": probe_redirects_sync,
    "examples_generated": probe_examples_generated,
    "volume_counts_agree": probe_volume_counts_agree,
    "py39_pinned": probe_py39_pinned,
    "readme_markers": probe_readme_markers,
    "judge_count": probe_judge_count,
    "submitlang_count": probe_submitlang_count, "result_count": probe_result_count,
    "verify_state": probe_verify_state, "topics": probe_topics,
    "topics_split": probe_topics_split, "no_flat_path": probe_no_flat_path,
    "topics_shape": probe_topics_shape, "topics_core_basis": probe_topics_core_basis,
    "topics_basis_consistent": probe_topics_basis_consistent,
    "lessons_indexed": probe_lessons_indexed,
    "ch5_table": probe_ch5_table,
    "dup_same_chapter": probe_dup_same_chapter,
    "prose_ratchet": probe_prose_ratchet,
    "problem_links": probe_problem_links,
    "problem_count_consistent": probe_problem_count_consistent,
    "anchors_registered": probe_anchors_registered,
    "io_pointer": probe_io_pointer,
    "reports_fresh": probe_reports_fresh,
}


# --------------------------------------------------------------- 断言执行

def run_assert(a: dict) -> tuple[bool, str]:
    kind = a["kind"]

    if kind in ("contains", "absent"):
        body = text(a["path"])
        if body is None:
            return False, f"文件不存在：{a['path']}"
        if a.get("section"):
            body = section_of(body, a["section"])
            if not body:
                return False, f"找不到小节「{a['section']}」"
        n = len(re.findall(a["pattern"], body, re.M))
        if kind == "contains":
            return n > 0, f"{a['path']} 命中 {n} 处"
        return n == 0, f"{a['path']} 命中 {n} 处（应为 0）"

    if kind == "each_contains":
        miss = []
        for rel in a["paths"]:
            body = text(rel)
            if body is None or not re.search(a["pattern"], body, re.M):
                miss.append(rel)
        if miss:
            return False, f"{len(a['paths'])} 份里有 {len(miss)} 份未命中：{miss}"
        return True, f"{len(a['paths'])} 份全部命中"

    if kind == "path_absent":
        p = ROOT / a["path"]
        return not p.exists(), ("不存在" if not p.exists() else f"仍存在：{a['path']}")

    if kind in ("mapping_has", "mapping_lacks"):
        qs = mapping().get(a["chapter"])
        if qs is None:
            return False, f"_mapping.json 里没有章 {a['chapter']}"
        got = a["problem"] in qs
        want = kind == "mapping_has"
        return got == want, f"{a['chapter']} {'含' if got else '不含'} {a['problem']}"

    if kind == "probe":
        fn = PROBES.get(a["name"])
        if fn is None:
            return False, f"未实现的探针：{a['name']}"
        return fn(a)

    return False, f"未知断言类型：{kind}"


def table_ids(rel: str, heading: str) -> set:
    """从正本的汇总表里抽决议 id，用来核对断言有没有漏写。"""
    body = text(rel) or ""
    sec = ""
    lines = body.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("#") and heading in ln:
            sec = "\n".join(lines[i:])
            break
    ids = set()
    for ln in sec.splitlines():
        m = re.match(r"^\|\s*\*{0,2}([A-Z])\*{0,2}\s*\|", ln)
        if m:
            ids.add(m.group(1))
    return ids


def main() -> int:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    verbose = "-v" in sys.argv

    rows, gaps = [], []
    n_ok = n_bad = n_todo = 0
    for g in spec["groups"]:
        declared = {d["id"] for d in g["decisions"]}
        if g.get("table_heading"):
            in_table = table_ids(g["source"], g["table_heading"])
            for miss in sorted(in_table - declared):
                gaps.append(f"决议 **{miss}** 在 `{g['source']}` 的汇总表里，但 `_decisions.json` 没有断言")
            for extra in sorted(declared - in_table):
                if len(extra) == 1:
                    gaps.append(f"断言里的决议 **{extra}** 在 `{g['source']}` 的汇总表里找不到")

        for d in g["decisions"]:
            todo = d.get("todo", "")
            for a in d["asserts"]:
                ok, detail = run_assert(a)
                if todo:
                    # 已拍板但排在后面批次的决议：断言现在必然失败，登记而不计分。
                    # 「现在做不了」不等于「不用登记」——忘掉它才是教训九说的那种错。
                    n_todo += (not ok)
                    rows.append((g["title"], d["id"], d["desc"], a.get("desc", ""),
                                 ok, detail + f"（排在 {todo}）"))
                    if not ok:
                        print(f"[待执行 {todo}] {d['id']}　{a.get('desc','')}　—— {detail}")
                    continue
                n_ok, n_bad = n_ok + ok, n_bad + (not ok)
                rows.append((g["title"], d["id"], d["desc"], a.get("desc", ""), ok, detail))
                if not ok or verbose:
                    print(f"[{'通过' if ok else '失败'}] {d['id']}　{a.get('desc','')}　—— {detail}")

    AUDIT.mkdir(parents=True, exist_ok=True)
    out = ["# 决议落实核对", "",
           "> 由 `scripts/check_decisions.py` 生成，断言表在 `dev/data/_decisions.json`，",
           "> 决议正本在 `dev/notes/拆分点.md`。**不要手改本文件。**", "",
           f"断言 {n_ok + n_bad} 条：通过 **{n_ok}**、失败 **{n_bad}**；",
           f"映射缺口 **{len(gaps)}** 条；",
           f"已拍板但尚未执行的决议里，**{n_todo}** 条断言暂时不成立（不计入退出码）。", ""]
    if gaps:
        out += ["## 映射缺口", "",
                "决议加进了正本却没写断言（或反过来）。写不出断言的决议说明它本身没定清楚。", ""]
        out += [f"- {g}" for g in gaps] + [""]
    cur = None
    for title, did, ddesc, adesc, ok, detail in rows:
        if title != cur:
            cur, _ = title, out.append(f"## {title}\n")
            out += ["| 决议 | 断言 | 结果 | 实测 |", "| --- | --- | --- | --- |"]
        out.append(f"| **{did}**　{ddesc} | {adesc} | {'✅' if ok else '❌'} | {detail} |")
    out.append("")
    REPORT.write_text("\n".join(out), encoding="utf-8")

    print(f"\n断言 {n_ok + n_bad} 条：通过 {n_ok}、失败 {n_bad}；映射缺口 {len(gaps)}")
    print(f"报告：{REPORT.relative_to(ROOT)}")
    return 1 if (n_bad or gaps) else 0


if __name__ == "__main__":
    raise SystemExit(main())
