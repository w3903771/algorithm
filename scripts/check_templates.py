"""正文模板代码盘点：数清「既不是完整题解、也没标片段」的代码段，为 P2 的抽取列清单。

输出 `dev/audit/模板代码盘点.md`。

**这个脚本有两个模式，现在只做第一个。**

| 模式 | 做什么 | 排在 |
| --- | --- | --- |
| **盘点**（本批） | 数清未验证的代码段，按章与模板类型分类，找出跨章重复的那些 | P0b |
| 编译测试 | `templates/` 建成之后，逐份编译 / 跑单测 | P2（02 §6.2） |

排序是有理由的：编译测试要读的 `templates/` 目录 **P2 才建**，
现在写就是「面向不存在的输入写检查器」——那正是 P0 原排序被推翻的同一个毛病。
盘点则只依赖现有正文，今天就能跑，而且它的产出正是 P2 抽取时要照着做的清单。

「未验证」这一档的口径与 00 号文件 §D8 完全一致，且**同源**：
已验证的那一档直接调 `verify_docs.executable_sections()`，
标了 `# [片段]` 的那一档按块内标记算。三处各写一遍必然漂移。

--------------------------------------------------------------------------
本脚本看不见什么
--------------------------------------------------------------------------
1. **代码对不对、能不能跑**。它一行都不执行。跑得起来的那 201 段归 `verify_docs.py`；
   剩下这 759 段**今天没有任何闸门**——这正是盘点它们的理由。
2. **该不该抽成模板**。「跨章重复」「够长」「有函数定义」是**信号**，不是判据。
   真正该进 `templates/` 的清单要人过一遍，脚本只负责把候选摆出来。
3. **模板类型分得准不准**。靠关键词表匹配代码与最近的标题，命中不了就记「未归类」——
   未归类的条数本身是个信号：它说明这段代码没有明显的算法特征。
4. **`templates/` 里的东西**。那个目录 P2 才建，本脚本现在不读它。
5. **C++ 轨**。现在正文里只有 15 个 `cpp` 块，双轨铺开排 P2/P4/P5；
   盘点照数，但「按类型分类」的关键词表是照 Python 正文写的。
6. **缩进块**。口径与 §D8 一致，只数**顶格**起始的围栏；Tab 里缩进的那 14 个块不计。

用法: uv run python scripts/check_templates.py
      uv run python scripts/check_templates.py -v    # 逐段打印
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
AUDIT = ROOT / "dev" / "audit"      # 脚本生成的报告：P-M② 起在 dev/audit/（02 §7.3）

REPORT = AUDIT / "模板代码盘点.md"

sys.path.insert(0, str(ROOT / "scripts"))
import verify_docs  # noqa: E402

FRAGMENT = "# [片段]"

# 模板类型的关键词表。左边是族名，右边命中代码或最近标题即算。
# 命不中就是「未归类」——那个数本身有意义，见文件头第 3 条。
FAMILIES = [
    ("树状数组", r"树状数组|lowbit|fenwick"),
    ("线段树", r"线段树|segment.?tree|懒标记|lazy"),
    ("分块 / ST 表", r"分块|ST 表|sparse.?table|块长"),
    ("并查集", r"并查集|dsu|find\(.*\).*parent|路径压缩"),
    ("堆 / 单调结构", r"heapq|单调栈|单调队列|deque\(\)"),
    ("字符串", r"KMP|next 数组|Manacher|Trie|字符串哈希|后缀"),
    ("图 · 最短路", r"Dijkstra|dijkstra|SPFA|Bellman|最短路"),
    ("图 · 生成树 / 连通性", r"最小生成树|Kruskal|Prim|Tarjan|强连通|割点|桥"),
    ("图 · 树上算法", r"LCA|倍增|树链剖分|dfs 序|树上差分"),
    ("图 · 匹配 / 网络流", r"匈牙利|二分图|网络流|最大流|增广"),
    ("搜索", r"BFS|DFS|双向搜索|迭代加深|IDA|剪枝|记忆化"),
    ("DP", r"dp\[|f\[i\]|背包|状压|区间 DP|树形 DP|滚动数组"),
    ("数学", r"快速幂|逆元|欧拉|筛|gcd|exgcd|组合数|矩阵"),
    ("基础算法", r"二分|前缀和|差分|双指针|离散化|排序"),
    ("IO / 工具", r"sys\.stdin|input = |setrecursionlimit|读入优化"),
]


def heading_of(lines: list, i: int) -> str:
    """最近的 `##` / `###` 标题，用来给代码段定位（报告里给人看的）。"""
    for j in range(i, -1, -1):
        if lines[j].startswith("#"):
            return lines[j].lstrip("# ").strip()
    return "（章首）"


def classify(code: str, heading: str) -> str:
    blob = code + "\n" + heading
    for name, pat in FAMILIES:
        if re.search(pat, blob, re.I):
            return name
    return "未归类"


def norm(code: str) -> str:
    """归一化后用来找跨章重复：去空行、去行尾空白、去注释。"""
    out = []
    for ln in code.splitlines():
        ln = re.sub(r"\s*#.*$", "", ln).rstrip()
        if ln.strip():
            out.append(ln)
    return "\n".join(out)


def collect() -> list:
    """回全部**顶格**代码块，每段带上分类所需的信息。"""
    verified = {(md.as_posix(), c) for md, _, c in verify_docs.executable_sections()}
    out = []
    for p in sorted(DOCS.rglob("*.md")):
        lines = p.read_text(encoding="utf-8").splitlines()
        i = 0
        while i < len(lines):
            m = re.match(r"^```(\w+)\s*$", lines[i])
            if not m:
                i += 1
                continue
            j = i + 1
            while j < len(lines) and not re.match(r"^```\s*$", lines[j]):
                j += 1
            code = "\n".join(lines[i + 1:j]) + "\n"
            state = ("片段" if FRAGMENT in code else
                     "已验证" if (p.as_posix(), code) in verified else "未验证")
            head = heading_of(lines, i)
            out.append(dict(file=p.relative_to(DOCS).as_posix(), line=i + 1,
                            lang=m.group(1), state=state, heading=head,
                            n=len([x for x in code.splitlines() if x.strip()]),
                            has_def=bool(re.search(r"^\s*(def|class) ", code, re.M)),
                            family=classify(code, head), norm=norm(code)))
            i = j + 1
    return out


def main(argv: list) -> int:
    blocks = [b for b in collect() if b["lang"] in ("python", "cpp")]
    rest = [b for b in blocks if b["state"] == "未验证"]

    # 跨章重复：同一段代码出现在两个以上的地方，是「模板独立成库」最直接的证据
    dup: dict = {}
    for b in rest:
        if b["n"] >= 4:
            dup.setdefault(b["norm"], []).append(b)
    dup = {k: v for k, v in dup.items() if len(v) > 1}

    by_family: dict = {}
    by_file: dict = {}
    for b in rest:
        by_family.setdefault(b["family"], []).append(b)
        by_file.setdefault(b["file"], []).append(b)

    AUDIT.mkdir(parents=True, exist_ok=True)
    def tally(lang: str) -> dict:
        sub = [b for b in blocks if b["lang"] == lang]
        return {s: sum(1 for b in sub if b["state"] == s)
                for s in ("已验证", "片段", "未验证")} | {"总": len(sub)}
    py, cpp = tally("python"), tally("cpp")
    L = ["# 模板代码盘点", "",
         "> 由 `scripts/check_templates.py` 生成。**不要手改本文件。**",
         "> 本批只做盘点；`templates/` 建成之后同一个脚本加编译测试模式（P2，02 §6.2）。", "",
         "| 轨 | 顶格代码块 | 已验证 | 标了片段 | **未验证且未声明** |",
         "| --- | --- | --- | --- | --- |",
         f"| Python | {py['总']} | {py['已验证']} | {py['片段']} | **{py['未验证']}** |",
         f"| C++ | {cpp['总']} | {cpp['已验证']} | {cpp['片段']} | **{cpp['未验证']}** |",
         f"| 合计 | {py['总'] + cpp['总']} | {py['已验证'] + cpp['已验证']} | "
         f"{py['片段'] + cpp['片段']} | **{py['未验证'] + cpp['未验证']}** |", "",
         "**Python 那一行就是 00 号文件 §D8 的三个数**——§D8 的口径只算 Python，"
         "本表多出的是 C++ 轨（双轨铺开排 P2/P4/P5，现在正文里只有这么几段）。",
         "已验证那一档两边同源，直接调 `verify_docs.executable_sections()`，不另算一遍。", "",
         "## 一、未验证代码段按模板类型分", "",
         "「未归类」不是分类失败的垃圾桶——它说明那段代码没有明显的算法特征，"
         "多半是讲解用的小例子（看「≥15 行」那一列就知道），抽模板时可以先跳过。", "",
         "| 模板类型 | 段数 | ≥15 行 | 有函数/类定义 | 涉及章数 |",
         "| --- | --- | --- | --- | --- |"]
    for fam, items in sorted(by_family.items(), key=lambda kv: -len(kv[1])):
        L.append(f"| {fam} | **{len(items)}** | {sum(b['n'] >= 15 for b in items)} | "
                 f"{sum(b['has_def'] for b in items)} | {len({b['file'] for b in items})} |")

    L += ["", "## 二、跨章重复的代码段（P2 抽取的第一批）", "",
          "同一段代码（去注释、去空行后逐字相同，且不少于 4 行）出现在两个以上的位置。",
          "**这是「模板独立成库」最直接的证据**：改一处就要记得改另一处，现在没人保证。", ""]
    if dup:
        L += ["| 段数 | 行数 | 出现在 |", "| --- | --- | --- |"]
        for k, v in sorted(dup.items(), key=lambda kv: -len(kv[1]))[:40]:
            L.append(f"| {len(v)} | {v[0]['n']} | "
                     + "；".join(f"`{b['file']}`:{b['line']}" for b in v[:4]) + " |")
        if len(dup) > 40:
            L.append(f"| … | | 另有 {len(dup) - 40} 组，见 `-v` 输出 |")
    else:
        L.append("无。")

    L += ["", "## 三、未验证代码段按章分", "",
          "抽模板时按这张表逐章过。「最长一段」是该章最值得先看的那一段。", "",
          "| 章 | 未验证段数 | 最长一段（行数 @ 行号） | 主要类型 |",
          "| --- | --- | --- | --- |"]
    for f, items in sorted(by_file.items(), key=lambda kv: -len(kv[1])):
        top = max(items, key=lambda b: b["n"])
        fams = sorted({b["family"] for b in items} - {"未归类"})
        L.append(f"| `{f}` | {len(items)} | {top['n']} @ {top['line']} | "
                 f"{'、'.join(fams[:3]) or '未归类'} |")
    L.append("")
    REPORT.write_text("\n".join(L), encoding="utf-8")

    if "-v" in argv:
        for b in rest:
            print(f"{b['file']}:{b['line']}  {b['n']} 行  {b['family']}  {b['heading']}")

    print(f"Python {py['总']} 段（已验证 {py['已验证']}、片段 {py['片段']}、"
          f"未验证 {py['未验证']}）＋ C++ {cpp['总']} 段（未验证 {cpp['未验证']}）")
    print(f"跨章重复 {len(dup)} 组，涉及 {sum(len(v) for v in dup.values())} 段")
    print(f"报告：{REPORT.relative_to(ROOT)}")
    return 0            # 盘点脚本不设阈值：它产出清单，不当闸门


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
