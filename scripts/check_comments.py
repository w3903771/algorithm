"""题解注释审计：结构 / 密度 / 转义陷阱 / 口吻 / 可执行代码零改动。

把 dev/spec/题解注释规范.md 里的硬性约束做成可执行检查，改注释的批次自查用。

用法:
  uv run python scripts/check_comments.py              # 审计全部题解
  uv run python scripts/check_comments.py BM           # 只审前缀匹配的
  uv run python scripts/check_comments.py --exact LC1  # 只审 LC1，不连带 LC11/LC128/LC1143
  uv run python scripts/check_comments.py --snapshot BM   # 改之前先存基线
  uv run python scripts/check_comments.py --diff BM       # 改之后比对基线
  uv run python scripts/check_comments.py --diff --git BM # 拿 git HEAD 当基线（更可靠）

`--diff` 是规范第一节那套 AST 比对的可执行版：解析成语法树、剥掉文档字符串
再比 `ast.dump()`。注释本来就不进语法树，所以只要有任何可执行语义的改动
就会暴露——改注释时误删一行代码、手滑改个变量名，都逃不掉。

**基线优先用 `--git`**：它拿 `git show HEAD:<file>` 当对照，谁都动不了。
`--snapshot` 存的文件基线有个致命弱点——改注释的人如果在改完之后又跑一次
`--snapshot`，基线就被改后的状态覆盖，`--diff` 于是变成自己跟自己比，
永远报「0 改动」，等于没查。所以 `--snapshot` 默认**拒绝覆盖已有条目**，
真要重存得显式加 `--force`。
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sol_store as store  # noqa: E402

BS = chr(92)                 # 源码里避免写字面反斜杠，免得自己也踩转义的坑

ROOT = Path(__file__).resolve().parent.parent
SOL = store.SOL
SNAP = ROOT / "sources" / "_tmp" / "comment_snapshot.json"

# 规范第三节要求的三段。第三段认「坑」的各种变体——既有语料里
# 「Python 的坑（本题必看）」「其它坑」都是它，只认字面「坑在哪」会误报。
REQUIRED = [("这题考什么", ["这题考什么"]),
            ("复杂度", ["数据规模与复杂度", "复杂度"]),
            ("坑", ["坑"])]

# 规范第二节：指向写作/调试过程的叙述，以及 AI 腔
TONE = ["上一版", "本书之前", "原本用的", "被证伪", "改稿", "之前写的",
        "值得注意的是", "综上所述", "让我们", "首先我们", "接下来我们",
        "需要注意的是，", "总而言之"]

# 未被转义的「反斜杠 + n」：前面不能是另一个反斜杠
LONE_NL = re.compile(r"(?<!" + re.escape(BS) + r")" + re.escape(BS) + r"[nN]")
# 反斜杠紧跟行尾 = 行继续符（中间允许有尾随空白）
LONE_CONT = re.compile(r"(?<!" + re.escape(BS) + r")" + re.escape(BS)
                       + r"[ \t]*\n")

# 规范第四节：文档字符串不是 raw 串，这些会被吞成控制字符
ESCAPES = [("\\b", "退格"), ("\\t", "制表"), ("\\a", "响铃"), ("\\f", "换页"),
           ("\\v", "垂直制表"), ("\\r", "回车")]

# 行内注释密度。既有 147 份 BISHI 的分布是 25 分位 5% / 中位 10% / 75 分位 15%，
# 所以 10% 只能当**参考线**（当提示报），5% 才是真正的下限（当错误报）——
# 规范点名的反例「90 行代码只有 6 条注释」正是 6.7%。
# 短文件不适用：十来行的题解全靠文档字符串讲清楚，硬凑注释反而是废话。
GOOD_DENSITY = 0.10
MIN_DENSITY = 0.05
DENSITY_MIN_LINES = 20


def norm(src: str) -> str:
    """剥掉全部文档字符串后的语法树指纹。注释不进语法树，所以只反映可执行语义。"""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            b = getattr(node, "body", None)
            if (b and isinstance(b[0], ast.Expr)
                    and isinstance(getattr(b[0], "value", None), ast.Constant)
                    and isinstance(b[0].value.value, str)):
                node.body = b[1:] or [ast.Pass()]
    return hashlib.sha1(ast.dump(tree).encode()).hexdigest()


def code_region(src: str, tree: ast.Module) -> list:
    """文档字符串之后的代码区行。密度只算这一段，不把文档字符串算进分母。"""
    lines = src.split("\n")
    start = 0
    if tree.body and isinstance(tree.body[0], ast.Expr) \
            and isinstance(getattr(tree.body[0], "value", None), ast.Constant) \
            and isinstance(tree.body[0].value.value, str):
        start = tree.body[0].end_lineno
    return lines[start:]


def audit(path: Path) -> tuple:
    """返回 (错误, 提示)。错误必须修；提示是参考线，由人判断值不值得动。"""
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return [f"语法错误：{exc}"], []
    doc = ast.get_docstring(tree) or ""
    issues, hints = [], []

    if not doc.strip():
        return ["无文档字符串"], []
    for name, alts in REQUIRED:
        if not any(a in doc for a in alts):
            issues.append(f"缺小节「{name}」")
    head = doc.split("\n", 1)[0]
    if "——" not in head and "—" not in head:
        issues.append("首行不是「题号 标题 —— 一句话」")
    if "写完记得替换" in doc or "TODO" in src:
        issues.append("残留占位符")

    # 规范第一节第 4 点：文档字符串不是 raw 串，反斜杠会被当转义处理。
    # 只报**真造成损坏**的——写成两个反斜杠是正确写法（渲染出字面的反斜杠n），
    # 一律报错会把已经写对的也拖下水。三种真损坏：
    #   1. 单个反斜杠 + n/N  -> 被吞成真换行，句子当场断成两截（BISHI84 曾如此）
    #   2. 单个反斜杠 + 换行 -> 行继续符，两行被悄悄拼成一行，ASCII 图整个塌掉
    #   3. 反斜杠 + b/t/a/f/v/r -> 被吞成控制字符
    doc_src = ast.get_source_segment(src, tree.body[0]) or ""
    if LONE_NL.search(doc_src):
        issues.append("文档字符串里有未转义的反斜杠 n，会被吞成真换行（写两个反斜杠才对）")
    if LONE_CONT.search(doc_src):
        issues.append("文档字符串里有反斜杠接换行（行继续符），两行会被悄悄拼成一行")

    for esc, what in ESCAPES:
        # 源码里写的是两个字符 \ 和 b；被吞掉后 doc 里会出现真的控制字符
        if esc.replace("\\", "") and ("\\" + esc[-1]) in src and esc[-1] not in "0123456789":
            if chr({"b": 8, "t": 9, "a": 7, "f": 12, "v": 11, "r": 13}[esc[-1]]) in doc:
                issues.append(f"转义陷阱：`{esc}` 被吞成{what}符")
    for w in TONE:
        if w in doc:
            issues.append(f"口吻残留：「{w}」")

    body = code_region(src, tree)
    nonblank = [l for l in body if l.strip()]
    comments = [l for l in nonblank if l.strip().startswith("#")]
    if len(nonblank) >= DENSITY_MIN_LINES:
        d = len(comments) / len(nonblank)
        msg = f"行内注释密度 {len(comments)}/{len(nonblank)} = {d * 100:.0f}%"
        if d < MIN_DENSITY:
            issues.append(f"{msg}，低于下限 {MIN_DENSITY:.0%}")
        elif d < GOOD_DENSITY:
            hints.append(f"{msg}，低于参考线 {GOOD_DENSITY:.0%}")
    return issues, hints


def targets(argv) -> list:
    """-> `[(题号, sol.py 路径)]`。

    P-M③ 起文件名一律是 `sol.py`，**题号在目录名上**——所以到处都得带着题号走，
    不能再拿 `path.stem` 当题号。基线快照也以题号为键（题号不随重组变，
    旧基线因此仍然有效；09 号文件 教训六）。
    """
    pats = [a for a in argv if not a.startswith("--")]
    # 与 verify.py 保持一致：默认按前缀匹配，--exact 只审点名的那几份。
    # 不加的话 `LC1` 会连带 LC11 / LC128 / LC1143，并行作业时看别人的半成品报错。
    exact = "--exact" in argv
    nos = store.all_numbers()
    if pats:
        nos = [n for n in nos
               if any(n == x or (not exact and n.startswith(x)) for x in pats)]
    return [(n, store.sol_path(n)) for n in nos]


def main(argv) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    files = targets(argv[1:])
    if not files:
        print("没有匹配的题解")
        return 0

    if "--snapshot" in argv:
        SNAP.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(SNAP.read_text(encoding="utf-8")) if SNAP.exists() else {}
        force = "--force" in argv
        added, kept = 0, []
        for no, p in files:
            if no in data and not force:
                kept.append(no)             # 已有基线不覆盖，见文件头的说明
                continue
            data[no] = norm(p.read_text(encoding="utf-8"))
            added += 1
        SNAP.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True),
                        encoding="utf-8")
        print(f"新增 {added} 份基线 -> {SNAP}")
        if kept:
            print(f"保留原有基线 {len(kept)} 份（要重存加 --force）：{' '.join(kept[:8])}"
                  + (" …" if len(kept) > 8 else ""))
        return 0

    if "--diff" in argv:
        use_git = "--git" in argv
        data = {}
        if use_git:
            import subprocess

            for no, p in files:
                rel = p.relative_to(ROOT).as_posix()
                r = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=str(ROOT),
                                   capture_output=True, text=True, encoding="utf-8")
                if r.returncode == 0:
                    data[no] = norm(r.stdout)
        elif SNAP.exists():
            data = json.loads(SNAP.read_text(encoding="utf-8"))
        else:
            print("没有基线。先跑 --snapshot，或改用 --diff --git")
            return 2
        changed, missing = [], []
        for no, p in files:
            if no not in data:
                missing.append(no)
                continue
            try:
                if norm(p.read_text(encoding="utf-8")) != data[no]:
                    changed.append(no)
            except SyntaxError as exc:
                changed.append(f"{no}（语法错误 {exc}）")
        for k in changed:
            print(f"  [!] {k} 的**可执行代码**被改动了")
        if missing:
            print(f"  [i] {len(missing)} 份没有基线：{' '.join(missing[:10])}")
        print(f"\n比对 {len(files)} 份，可执行代码有改动的 {len(changed)} 份")
        return 1 if changed else 0

    quiet = "--errors-only" in argv
    bad, warn = {}, {}
    for no, p in files:
        iss, hints = audit(p)
        if iss:
            bad[no] = iss
        if hints and not quiet:
            warn[no] = hints
    for k, v in bad.items():
        print(f"  [错误] {k}")
        for i in v:
            print(f"         {i}")
    for k, v in warn.items():
        print(f"  [提示] {k}: {'；'.join(v)}")
    print(f"\n审计 {len(files)} 份：错误 {len(bad)} 份，提示 {len(warn)} 份")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
