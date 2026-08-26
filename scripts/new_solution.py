"""按题目签名生成题解骨架 -> solutions/<site>/<题号>/（**不含任何解法**）。

核心代码模式的题解必须严格对上函数名、参数名、参数个数，写错就是一次
无谓的 RE。这些信息抓题面时已经拿到了（力扣的 metaData、牛客的 Java 模板），
没道理让人再去页面上抄一遍。

生成的骨架包含：
  - 文档字符串头（题号 / 标题 / 链接 / 难度 / 判题模式），站点题解页会把它渲染成
    「一句话 + 解题思路」，所以留好了小节标题
  - 带类型注解的 `class Solution` 与方法签名（设计题给构造函数与全部方法）
  - `# TODO` 占位，跑 verify 会直接失败，不会被误当成已完成

同时落一份 `meta.json`。P-M③ 起题目的存在性以 `meta.json` 为准
（`sol_store.all_numbers()`），只写 `sol.py` 的话没有一个消费方看得见它。

用法:
  uv run python scripts/new_solution.py LC1            # 生成一个
  uv run python scripts/new_solution.py LC1 LC15 BM1   # 生成多个
  uv run python scripts/new_solution.py --set hot100   # 生成整套题单里还没写的
  uv run python scripts/new_solution.py --force LC1    # 覆盖已存在的（慎用）
  uv run python scripts/new_solution.py --stdout LC1   # 只打印不落盘
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sol_store as store  # noqa: E402
from migrate_solutions import fresh_meta  # noqa: E402

ROOT = store.ROOT
DOCS = ROOT / "docs"
DATA = store.DATA                   # 公开数据：见 sol_store.DATA
SOL = store.SOL

# 本仓库统一类型词表 -> Python 注解
PY_TYPE = {
    "integer": "int", "long": "int", "double": "float", "boolean": "bool",
    "character": "str", "string": "str", "void": "None",
    "integer[]": "List[int]", "long[]": "List[int]", "double[]": "List[float]",
    "boolean[]": "List[bool]", "character[]": "List[str]", "string[]": "List[str]",
    "integer[][]": "List[List[int]]", "double[][]": "List[List[float]]",
    "character[][]": "List[List[str]]", "string[][]": "List[List[str]]",
    "list<integer>": "List[int]", "list<string>": "List[str]",
    "list<list<integer>>": "List[List[int]]", "list<list<string>>": "List[List[str]]",
    # 节点类型的注解**加引号**：ListNode / TreeNode 是判题环境注入的，模块里并不存在，
    # 不加引号会在 def 求值时 NameError。加引号（而不是 `from __future__ import
    # annotations`）是因为力扣会在提交的代码前拼前导代码，future 导入永远不在首行，
    # 一提交就 SyntaxError。
    "ListNode": '"Optional[ListNode]"', "TreeNode": '"Optional[TreeNode]"',
    "ListNode[]": '"List[Optional[ListNode]]"', "TreeNode[]": '"List[Optional[TreeNode]]"',
    "list<ListNode>": '"List[Optional[ListNode]]"',
    "list<Interval>": '"List[Interval]"', "Interval": '"Interval"',
}
MODE_CN = {"acm": "ACM（读 stdin 写 stdout）", "core": "核心代码模式"}


def py_type(t: str) -> str:
    return PY_TYPE.get((t or "").strip(), "object")


def load_sets() -> tuple:
    d = json.loads((DATA / "_sources.json").read_text(encoding="utf-8"))
    return d["sites"], [s for s in d["sets"] if (ROOT / s["list"]).exists()]


def load_all() -> dict:
    """题号 -> (题单配置, 题单条目, 题面 JSON)。"""
    sites, sets_ = load_sets()
    out = {}
    for s in sets_:
        raw = ROOT / s["raw"]
        for it in json.loads((ROOT / s["list"]).read_text(encoding="utf-8")):
            f = raw / f"{it['no']}.json"
            data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
            out[it["no"]] = (s, it, data, sites[s["site"]])
    return out


def sig_lines(func: dict) -> list:
    """签名 -> class Solution 的方法定义（题解要照着填的那部分）。"""
    if func.get("kind") == "design":
        cls = func.get("classname") or "Solution"
        L = [f"class {cls}:"]
        ctor = (func.get("constructor") or {}).get("params") or []
        args = "".join(f", {p['name']}: {py_type(p['type'])}" for p in ctor)
        L += [f"    def __init__(self{args}):", "        # TODO", "        ...", ""]
        for m in func.get("methods") or []:
            args = "".join(f", {p['name']}: {py_type(p['type'])}" for p in m.get("params") or [])
            L += [f"    def {m['name']}(self{args}) -> {py_type((m.get('return') or {}).get('type'))}:",
                  "        # TODO", "        ...", ""]
        return L[:-1]

    methods = func.get("methods") if func.get("kind") == "multi" else [func]
    L = ["class Solution:"]
    for m in methods:
        args = "".join(f", {p['name']}: {py_type(p['type'])}" for p in m.get("params") or [])
        ret = py_type((m.get("return") or {}).get("type"))
        L += [f"    def {m['name']}(self{args}) -> {ret}:", "        # TODO", "        ...", ""]
    return L[:-1]


def hint_line(no: str, s: dict, it: dict, func: dict, site: dict) -> str:
    """生成时打到终端的提示行——**不写进文件**。

    来源、难度、链接站点上都有（页头的 chips 与「原题」链接），签名就写在
    紧接着的代码里，全都往文件里再抄一遍只会让站点正文多出一段重复内容。
    既有 165 份题解也不带这些。作者需要的时候看终端这一行就够了。
    """
    sig = ""
    if func.get("kind") == "function":
        params = "、".join(f"{p['name']}: {p['type']}" for p in func.get("params") or [])
        sig = f"　{func.get('name')}({params}) -> {(func.get('return') or {}).get('type')}"
    elif func.get("kind") == "design":
        sig = (f"　设计题 class {func.get('classname')}："
               f"{'、'.join(m['name'] for m in func.get('methods') or [])}")
    elif func.get("kind") == "multi":
        sig = (f"　需实现 {'、'.join(m['name'] for m in func.get('methods') or [])}，"
               "判题走该题目录里的 driver.py")
    return f"{site['name']} · {s['name']}　{it.get('difficulty', '')}{sig}\n     {it.get('url', '')}"


def skeleton(no: str, s: dict, it: dict, data: dict, site: dict) -> str:
    """按 dev/spec/题解注释规范.md 第三节的三段结构生成骨架。

    三段（这题考什么 / 数据规模与复杂度 / 坑在哪）是硬性要求，所以骨架里
    先把小节标题摆好，免得写的时候漏掉——审计脚本 check_comments.py 会查。
    """
    func = data.get("func") or {}
    title = it.get("title") or no
    L = [f'"""{no} {title} —— 一句话说清这题在求什么（写完记得替换这行）。', "",
         "这题考什么：",
         "    TODO：点破核心观察或模型归约，讲清**为什么**是这个算法。",
         "",
         "数据规模与复杂度：",
         "    TODO：列出关键上界，推出复杂度，说明为什么够用、朴素做法为什么不够。",
         "",
         "坑在哪：",
         "  1. TODO：每条都要说清「不这么写会怎样」。",
         '"""']
    if s["mode"] != "core":
        return "\n".join(L + ["", "", "# TODO: 读 stdin、算、写 stdout", ""])
    L += ["from typing import List, Optional", "", ""]
    L += sig_lines(func) if func else ["class Solution:", "    # TODO", "    ..."]
    return "\n".join(L) + "\n"


def main(argv) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    flags = {a for a in argv[1:] if a.startswith("--")}
    args = [a for a in argv[1:] if not a.startswith("--")]
    force, to_stdout = "--force" in flags, "--stdout" in flags

    allq = load_all()
    targets = []
    if "--set" in argv:
        key = argv[argv.index("--set") + 1]
        targets = [no for no, (s, *_) in allq.items() if s["key"] == key]
        args = [a for a in args if a != key]
    targets += [a for a in args if a in allq]
    unknown = [a for a in args if a not in allq]
    for a in unknown:
        print(f"[跳过] {a} 不在任何已抓取的题单里")
    if not targets:
        print("没有匹配的题目。用法见文件头。")
        return 1

    def key(n):
        return ("".join(c for c in n if c.isalpha()),
                int("".join(c for c in n if c.isdigit()) or 0))

    made = skipped = 0
    for no in sorted(set(targets), key=key):
        s, it, data, site = allq[no]
        text = skeleton(no, s, it, data, site)
        if to_stdout:
            print(f"# ===== {no} =====")
            print(text)
            continue
        out = store.sol_path(no)
        if out.exists() and not force:
            skipped += 1
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        # meta.json 只在缺失时新建。--force 重发的是**骨架**，不该顺手把
        # judge（判题配置）与 langs（判题机记录）清零——那两项是手工/提交脚本写的，
        # 重生成不出来。P-M③ 前它们在全局 JSON 里，--force 天然碰不到。
        if not store.meta_path(no).exists():
            store.save_meta(no, fresh_meta(no))
        print(f"[生成] {out.parent.relative_to(ROOT)}/  {it.get('title', '')}")
        # 来源/链接/签名只打到终端，不写进文件（见 hint_line 的说明）
        print(f"     {hint_line(no, s, it, data.get('func') or {}, site)}")
        made += 1
    if not to_stdout:
        print(f"\n生成 {made}，跳过(已存在) {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
