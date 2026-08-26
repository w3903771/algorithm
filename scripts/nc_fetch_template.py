"""抓牛客核心代码模式题目的**函数签名**与官方样例 -> sources/05-nowcoder/templates/

为什么要单开一个脚本：力扣的 GraphQL 直接给 `metaData`（函数名、参数类型、返回类型），
牛客**没有对应接口**。题面页 HTML 里的 `class Solution` 全是社区 Java 题解，不是模板；
真正的模板藏在题目页的编辑器状态里：

    window.__ncMonacoEditorApi.editorParams.questionInfo.supportLanguages[].template

所以只能开浏览器等 Monaco 初始化后把它读出来。同一处还带 `samples`/`testcases`，
比题面解析出来的更权威（题面是渲染后的 HTML，样例里的空白与换行常被吃掉）。

签名从 **Java 模板**解析，不从 Python3 模板：Python 模板只有形参名没有类型，
而判题要靠类型把 `{1,2,3}` 还原成链表还是数组。Java 模板写的是
`public ListNode ReverseList (ListNode head)`，类型齐全。

产物：
  sources/05-nowcoder/templates/BM<n>.json   模板原文 + 样例 + 解析出的 func
并把 `func` 与官方 `examples` 合并回 sources/05-nowcoder/raw/BM<n>.json，
让下游（corejudge / verify）对牛客与力扣用同一套字段。

需要先登录一次（uv run python scripts/nc_login.py）。

用法:
  uv run python scripts/nc_fetch_template.py            # 全部核心代码模式题单
  uv run python scripts/nc_fetch_template.py --limit 3  # 只跑前 3 题（调试）
  uv run python scripts/nc_fetch_template.py BM1 BM100  # 只跑指定题
  uv run python scripts/nc_fetch_template.py --force    # 忽略已存在，重抓
  uv run python scripts/nc_fetch_template.py --reparse  # 不联网，用存下来的模板重解析签名
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DATA = ROOT / "data"        # 公开数据：站点构建与 check_prose 要读，随仓库发布
NC = ROOT / "sources" / "05-nowcoder"
TPL = NC / "templates"
RAW = NC / "raw"
AUTH = ROOT / ".auth" / "nowcoder.json"
TPL.mkdir(parents=True, exist_ok=True)

# Java 类型 -> 本仓库统一的类型词表（与力扣 metaData 的 type 对齐）
JAVA2TYPE = {
    "int": "integer", "Integer": "integer", "long": "long", "Long": "long",
    "double": "double", "Double": "double", "float": "double",
    "boolean": "boolean", "Boolean": "boolean",
    "char": "character", "Character": "character",
    "String": "string", "void": "void",
    "int[]": "integer[]", "Integer[]": "integer[]", "int[][]": "integer[][]",
    "long[]": "long[]", "double[]": "double[]", "double[][]": "double[][]",
    "boolean[]": "boolean[]", "char[]": "character[]", "char[][]": "character[][]",
    "String[]": "string[]", "String[][]": "string[][]",
    "ListNode": "ListNode", "ListNode[]": "ListNode[]",
    "TreeNode": "TreeNode", "TreeNode[]": "TreeNode[]",
    "Interval": "Interval", "Point": "Point", "RandomListNode": "RandomListNode",
    "TreeLinkNode": "TreeLinkNode",
    "ArrayList<Integer>": "list<integer>", "List<Integer>": "list<integer>",
    "ArrayList<String>": "list<string>", "List<String>": "list<string>",
    "ArrayList<ArrayList<Integer>>": "list<list<integer>>",
    "List<List<Integer>>": "list<list<integer>>",
    "ArrayList<ArrayList<String>>": "list<list<string>>",
    "List<List<String>>": "list<list<string>>",
}

# Java 类型：允许**一层嵌套**泛型。`[^>]*` 会在 ArrayList<ArrayList<Integer>> 的
# 第一个 `>` 就收手，BM26/BM54 那种返回值因此整条匹配不上。
GTYPE = r"[A-Za-z_][\w.]*(?:\s*<[^<>]*(?:<[^<>]*>[^<>]*)*>)?(?:\s*\[\s*\])*"
# <修饰符?> <返回类型> <方法名> (<形参表>) { —— 模板里方法名与括号之间常有空格。
# 修饰符是可选的：BM39「序列化二叉树」的两个方法就是包级私有，没写 public。
# 结尾必须跟 `{`，否则 `if (…)`、`return foo(…)` 之类会被误当成方法。
METHOD = re.compile(
    rf"(?:(?:public|private|protected|static|final)\s+)*({GTYPE})\s+"
    rf"([A-Za-z_]\w*)\s*\(([^)]*)\)\s*(?:throws\s+[\w,\s.]+)?\{{", re.M)
CTOR = re.compile(r"public\s+Solution\s*\(([^)]*)\)")
CLASS_BODY = re.compile(r"public\s+class\s+Solution\b")
# 控制结构长得像方法声明，别当成签名
KEYWORDS = {"if", "for", "while", "switch", "catch", "synchronized", "return",
            "new", "else", "do", "try", "class", "interface", "enum"}

_GENERIC = re.compile(r"^(?:java\.util\.)?(?:ArrayList|List|Collection|Iterable)<(.+)>$")


def norm_java_type(t: str) -> str:
    t = re.sub(r"\s+", "", t or "")
    if t in JAVA2TYPE:
        return JAVA2TYPE[t]
    # 词表没收的容器类型按 `list<元素类型>` 递归归一，
    # 这样 ArrayList<ListNode>、ArrayList<Interval> 这类也能拿到结构信息
    m = _GENERIC.match(t)
    if m:
        return f"list<{norm_java_type(m.group(1))}>"
    return JAVA2TYPE.get(t, t)


def parse_params(sig: str) -> list:
    """`int[] numbers, int target` -> [{'name':'numbers','type':'integer[]'}, …]

    数组维度**可能写在参数名后面**（C 风格：`int A[]`），牛客的老模板就这么写。
    只认 `int[] A` 会把这类参数整条丢掉——BM87 的签名因此只剩 m、n 两个 int，
    A、B 两个数组凭空消失，骨架跟着生成成 `merge(self, m, n)`。
    这里把后置的 `[]` 归并回类型上。
    """
    out = []
    for part in [p.strip() for p in split_top(sig, ",") if p.strip()]:
        m = re.match(r"^(.*?[\w>\]])\s+([A-Za-z_]\w*)((?:\s*\[\s*\])*)\s*$", part)
        if not m:
            continue
        out.append({"name": m.group(2),
                    "type": norm_java_type(m.group(1) + m.group(3))})
    return out


def split_top(s: str, sep: str) -> list:
    """按分隔符切，但跳过 <>、[]、() 与字符串里的分隔符（泛型参数里也有逗号）。"""
    out, buf, depth, in_str, quote, esc = [], [], 0, False, "", False
    for ch in s or "":
        if in_str:
            buf.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                in_str = False
            continue
        if ch in "\"'":
            in_str, quote = True, ch
        elif ch in "<[({":
            depth += 1
        elif ch in ">])}":
            depth -= 1
        if ch == sep and depth == 0:
            out.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    out.append("".join(buf))
    return out


def parse_java_template(java: str) -> dict:
    """Java 模板 -> 与力扣 metaData 同构的 func 描述。

    两种形态：
      普通函数题  public class Solution { public int[] twoSum (int[] a, int t) {…} }
      设计题      public class Solution { public Solution(int capacity){…}
                                          public int get(int key){…} … }
    设计题靠「有 public Solution(...) 构造函数」判定。
    """
    if not java:
        return {"kind": "unknown", "nparams": 0}
    body = java[CLASS_BODY.search(java).end():] if CLASS_BODY.search(java) else java
    ctor = CTOR.search(body)
    methods = [m for m in METHOD.finditer(body)
               if m.group(2) != "Solution" and m.group(1).split("<")[0] not in KEYWORDS]

    if ctor:
        return {
            "kind": "design",
            "classname": "Solution",
            "constructor": {"params": parse_params(ctor.group(1))},
            "methods": [{"name": m.group(2), "params": parse_params(m.group(3)),
                         "return": {"type": norm_java_type(m.group(1))}} for m in methods],
            # 牛客设计题的判题输入是「操作名数组, 参数数组, 构造参数…」
            "nparams": 2 + len(parse_params(ctor.group(1))),
        }
    if not methods:
        return {"kind": "unknown", "nparams": 0}

    def desc(m):
        params = parse_params(m.group(3))
        return {"name": m.group(2), "params": params,
                "return": {"type": norm_java_type(m.group(1))}, "nparams": len(params)}

    if len(methods) > 1:
        # 要求实现多个方法且互相咬合的题（BM39 序列化二叉树：Serialize 后再 Deserialize）。
        # 调用顺序是题目语义，猜不出来，交给该题目录里的 spj.py 自定义判题。
        return {"kind": "multi", "methods": [desc(m) for m in methods],
                "nparams": desc(methods[0])["nparams"]}
    return {"kind": "function", **desc(methods[0])}


def load_targets(argv) -> tuple:
    d = json.loads((DATA / "_sources.json").read_text(encoding="utf-8"))
    core = [s for s in d["sets"]
            if s["mode"] == "core" and s["site"] == "nowcoder" and (ROOT / s["list"]).exists()]
    items = []
    for s in core:
        items += json.loads((ROOT / s["list"]).read_text(encoding="utf-8"))
    only = [a for a in argv[1:] if not a.startswith("-")]
    if only:
        items = [it for it in items if it["no"] in only]
    if "--limit" in argv:
        items = items[:int(argv[argv.index("--limit") + 1])]
    return items, "--force" in argv


def merge_into_raw(no: str, func: dict, samples: list) -> None:
    """把签名与官方样例并回 raw/BM*.json，字段名与力扣那边保持一致。"""
    p = RAW / f"{no}.json"
    if not p.exists():
        return
    d = json.loads(p.read_text(encoding="utf-8"))
    d["func"] = func
    if samples:
        # 官方 samples 比题面 HTML 解析出来的可靠：题面里的空白与换行会被渲染吃掉
        d["examples"] = [{"name": f"示例{s.get('index') or i + 1}",
                          "input": (s.get("input") or "").strip(),
                          "output": (s.get("output") or "").strip(),
                          "note": (s.get("note") or "").strip(),
                          "raw_input": (s.get("input") or "").strip(),
                          "aligned": True}
                         for i, s in enumerate(samples)]
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def reparse_all(items) -> int:
    """不联网，用已存下的 Java 模板重新解析签名。

    解析正则每改进一次（嵌套泛型、无修饰符方法……）都得让存量跟上，
    重抓 101 个页面要七八分钟，而模板原文早就在本地了。
    """
    stats, n = {}, 0
    for it in items:
        p = TPL / f"{it['no']}.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        func = parse_java_template((d.get("templates") or {}).get("Java", ""))
        if func != d.get("func"):
            print(f"  [更新] {it['no']} {it['title']}: "
                  f"{(d.get('func') or {}).get('kind')} -> {func['kind']}")
            n += 1
        d["func"] = func
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        merge_into_raw(it["no"], func, d.get("samples") or [])
        stats[func["kind"]] = stats.get(func["kind"], 0) + 1
    print(f"\n重解析 {sum(stats.values())} 题，其中 {n} 题签名有变化")
    print("签名类型:", "、".join(f"{k} {v}" for k, v in stats.items() if v))
    return 0


def main(argv) -> int:
    items, force = load_targets(argv)
    if not items:
        print("没有匹配的题目")
        return 0
    if "--reparse" in argv:
        return reparse_all(items)

    from playwright.sync_api import sync_playwright

    if not AUTH.exists():
        print("[warn] 未登录（.auth/nowcoder.json 不存在）。题目页可能拿不到编辑器状态，")
        print("       先跑一次 uv run python scripts/nc_login.py")

    ok = skip = fail = 0
    stats = {"function": 0, "design": 0, "unknown": 0}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(storage_state=str(AUTH) if AUTH.exists() else None)
        page = ctx.new_page()
        for it in items:
            out = TPL / f"{it['no']}.json"
            if out.exists() and not force:
                d = json.loads(out.read_text(encoding="utf-8"))
                stats[d.get("func", {}).get("kind", "unknown")] = \
                    stats.get(d.get("func", {}).get("kind", "unknown"), 0) + 1
                merge_into_raw(it["no"], d["func"], d.get("samples") or [])
                skip += 1
                continue
            src = urllib.parse.quote(
                f"/exam/oj?questionJobId=10&topicId={it['tpId']}", safe="")
            url = (f"https://www.nowcoder.com/practice/{it['uuid']}"
                   f"?tpId={it['tpId']}&tqId={it['questionId']}&sourceUrl={src}")
            qi = None
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                # Monaco 是异步起的，questionInfo 要等它挂到 window 上
                for _ in range(25):
                    time.sleep(1)
                    qi = page.evaluate(
                        "()=>{try{return window.__ncMonacoEditorApi.editorParams"
                        ".questionInfo}catch(e){return null}}")
                    if qi:
                        break
            except Exception as exc:
                print(f"  [ERR] {it['no']} {it['title']}: {exc}")
            if not qi:
                print(f"  [FAIL] {it['no']} {it['title']}  编辑器状态没拿到")
                fail += 1
                continue

            tpls = {L["langName"]: L.get("template") or ""
                    for L in (qi.get("supportLanguages") or [])}
            func = parse_java_template(tpls.get("Java", ""))
            stats[func["kind"]] = stats.get(func["kind"], 0) + 1
            samples = qi.get("samples") or qi.get("testcases") or []
            out.write_text(json.dumps({
                "no": it["no"], "title": it["title"], "uuid": it["uuid"],
                "judgeType": qi.get("judgeType"), "type": qi.get("type"),
                "timeLimit": qi.get("timeLimit"), "memoryLimit": qi.get("memoryLimit"),
                "func": func,
                "templates": {k: v for k, v in tpls.items() if k in ("Java", "Python3", "Python 3")},
                "samples": samples,
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            merge_into_raw(it["no"], func, samples)
            ok += 1
            if func["kind"] == "unknown":
                print(f"  [warn] {it['no']} {it['title']}  签名没解析出来")
            if ok % 10 == 0:
                print(f"  ... 已抓 {ok} 题 (最新 {it['no']} {it['title']})")
        browser.close()

    print(f"\n成功 {ok}，跳过(已存在) {skip}，失败 {fail}")
    print("签名类型:", "、".join(f"{k} {v}" for k, v in stats.items() if v))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
