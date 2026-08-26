"""抽取教程正文里的例题代码块，用官方样例实测，确保「书上印的代码真能跑对」。

规则：在某章的 `### <题号> ...` 小节里，取**最长**的 ```python 代码块；
若该代码块含 `input()` 或 `sys.stdin`（即像一份完整题解），就拿去跑样例。

若某个代码块只是讲解片段而非完整题解，在块内加一行标记即可跳过：

    # [片段]

判定方式沿用题解那一套：读各题 `meta.json` 的 `judge` 字段，
spj 题调用该题目录里 `spj.py` 的 `check(inp, out)`，浮点题按 eps 比对，其余严格比对。

用法:
  uv run python scripts/verify_docs.py                 # 全部章节
  uv run python scripts/verify_docs.py ds/            # 只查路径含该串的章节
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sol_store as store  # noqa: E402

ROOT = store.ROOT
DOCS = ROOT / "docs"
AUDIT = ROOT / "dev" / "audit"      # 脚本生成的报告：P-M② 起在 dev/audit/（02 §7.3）
RAW = ROOT / "sources" / "05-nowcoder" / "raw"
TMP = ROOT / "sources" / "_tmp" / "docs_code"
REPORT = AUDIT / "正文代码验证报告.md"
STATE = ROOT / "sources" / "_tmp" / "docs_verify_state.json"

# 同 verify.py：spj.py 由 importlib 从**题目录**加载，别在 29 个入库目录里撒 __pycache__
sys.dont_write_bytecode = True

SEC = re.compile(r"^#{2,4}\s+((?:BISHI|PIO)\d+)\b", re.M)
CODE = re.compile(r"```python\n(.*?)```", re.S)
FRAGMENT = "# [片段]"


def load_judge() -> dict:
    """`{题号: judge 配置}`。P-M③ 前是全局 solutions/_judge.json。"""
    return store.judge_cfg()


def load_spj(no: str):
    p = store.spj_path(no)
    if not p.exists():
        return None
    spec = importlib.util.spec_from_file_location("spjdoc_" + no, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "check", None)


def norm(s: str) -> list:
    return [ln.rstrip() for ln in s.replace("\r\n", "\n").rstrip("\n").split("\n")]


def same(exp: str, got: str, mode: str, eps: float, checker, inp: str) -> bool:
    if mode == "spj" and checker is not None:
        try:
            return bool(checker(inp, got))
        except Exception:
            return False
    if mode == "float":
        a, b = exp.split(), got.split()
        if len(a) != len(b):
            return False
        for x, y in zip(a, b):
            if x == y:
                continue
            try:
                fx, fy = float(x), float(y)
            except ValueError:
                return False
            if abs(fx - fy) > eps * max(1.0, abs(fx)):
                return False
        return True
    return norm(exp) == norm(got)


def check_one(md: Path, no: str, code: str, judge: dict) -> dict:
    raw = RAW / (no + ".json")
    if not raw.exists():
        return {"file": md.relative_to(DOCS).as_posix(), "no": no, "status": "NO_PROBLEM"}
    data = json.loads(raw.read_text(encoding="utf-8"))
    examples = data.get("examples") or []
    if not examples:
        return {"file": md.relative_to(DOCS).as_posix(), "no": no, "status": "NO_SAMPLE"}

    cfg = judge.get(no, {})
    mode = cfg.get("mode", "exact")
    eps = cfg.get("eps", 1e-6)
    checker = load_spj(no) if mode == "spj" else None
    if mode == "spj" and checker is None:
        mode = "exact"

    TMP.mkdir(parents=True, exist_ok=True)
    src = TMP / (md.stem + "__" + no + ".py")
    src.write_text(code, encoding="utf-8")

    for i, ex in enumerate(examples, 1):
        inp = ex.get("input", "")
        if not inp.endswith("\n"):
            inp += "\n"
        try:
            r = subprocess.run([sys.executable, str(src)], input=inp, capture_output=True,
                               text=True, timeout=15, encoding="utf-8")
        except subprocess.TimeoutExpired:
            return {"file": md.relative_to(DOCS).as_posix(), "no": no, "status": "TLE", "case": i, "mode": mode}
        if r.returncode != 0:
            return {"file": md.relative_to(DOCS).as_posix(), "no": no, "status": "RE", "case": i, "mode": mode,
                    "detail": (r.stderr or "").strip()[-400:]}
        if not same(ex.get("output", ""), r.stdout, mode, eps, checker, inp):
            return {"file": md.relative_to(DOCS).as_posix(), "no": no, "status": "WA", "case": i, "mode": mode,
                    "detail": "期望 {!r} / 实际 {!r}".format(
                        ex.get("output", "").strip()[:100], r.stdout.strip()[:100])}
    return {"file": md.relative_to(DOCS).as_posix(), "no": no, "status": "PASS", "cases": len(examples), "mode": mode}


def executable_sections(pat: str = "") -> list:
    """回 `[(章文件, 题号, 代码)]`——正文里「像一份完整题解」的代码块。

    规则：在某章的 `### <题号>` 小节里，取**含 `input()`/`sys.stdin` 且没标片段的
    最长** ```python 块。抽取口径只有这一份实现，`check_prose.py` 数「未验证代码段」
    时直接调它——两处各写一遍必然漂移，而那个数会被写进 00 号文件 §D8。
    """
    out = []
    for md in sorted(DOCS.rglob("*.md")):
        rel = md.relative_to(DOCS).as_posix()
        if pat and pat not in rel:
            continue
        text = md.read_text(encoding="utf-8")
        marks = list(SEC.finditer(text))
        for i, m in enumerate(marks):
            end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
            blocks = [b for b in CODE.findall(text[m.end():end])
                      if ("input()" in b or "sys.stdin" in b) and FRAGMENT not in b]
            if blocks:
                out.append((md, m.group(1), max(blocks, key=len)))
    return out


def main(argv) -> int:
    pat = argv[1] if len(argv) > 1 else ""
    judge = load_judge()
    results = []
    for md, no, code in executable_sections(pat):
        results.append(check_one(md, no, code, judge))

    # 累积结果只为「带过滤参数跑一部分章节」服务：那时不该覆盖其它章节的历史结论。
    #
    # **全量跑（无过滤参数）时整表重建**，不与旧状态合并。合并过一次就知道为什么：
    #   · P-M① 改了全部 74 章的文件名，旧键一条不掉，报告成了 202 旧 + 202 新 = 403；
    #   · P-M② 拆章把 BISHI7 从 ds/hash.md 搬到 string/hash.md，两个文件都还在，
    #     「按文件是否存在剔键」也剔不掉那条旧的，报告又多出 1 条。
    # 路径改动是这个仓库的常态，任何「靠增量收敛」的写法都会被下一次搬家打破；
    # 全量跑本来就有完整结论，直接以它为准最省心。
    STATE.parent.mkdir(parents=True, exist_ok=True)
    state = {}
    if pat and STATE.exists():
        try:
            state = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            state = {}
        # 局部跑也要顺手剔掉指向已消失文件的键
        state = {k: v for k, v in state.items() if (DOCS / k.split("::")[0]).exists()}
    for r in results:
        state[r["file"] + "::" + r["no"]] = r
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    results = [state[k] for k in sorted(state)]
    npass = sum(r["status"] == "PASS" for r in results)
    bad = [r for r in results if r["status"] not in ("PASS", "NO_PROBLEM", "NO_SAMPLE")]

    L = ["# 正文例题代码验证报告\n",
         "> 由 `scripts/verify_docs.py` 生成：把教程正文里的完整题解代码块抽出来，",
         "> 用该题的官方样例实测，判定规则与题解那一套（各题 `meta.json` 的 `judge`）一致。",
         "> 讲解片段（标了 `# [片段]`）不参与验证。\n",
         "**{} 通过　{} 失败**（共检出 {} 段可执行代码）\n".format(npass, len(bad), len(results)),
         "| 章节 id | 题号 | 结果 | 判定 | 样例数 |", "| --- | --- | --- | --- | --- |"]
    for r in results:
        icon = "✅ PASS" if r["status"] == "PASS" else "❌ " + r["status"]
        L.append("| {} | {} | {} | {} | {} |".format(
            r["file"], r["no"], icon, r.get("mode", "-"), r.get("cases", "-")))
    if bad:
        L.append("\n## 失败明细\n")
        for r in bad:
            L.append("- **{} / {}** — {}（样例 {}）\n\n  ```\n  {}\n  ```".format(
                r["file"], r["no"], r["status"], r.get("case", "?"), r.get("detail", "")))
    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")

    for r in results:
        mark = "  ok  " if r["status"] == "PASS" else " {} ".format(r["status"])
        print("[{}] {:<44} {}".format(mark, r["file"], r["no"]))
    print("\n通过 {} / 失败 {}　报告 -> {}".format(npass, len(bad), REPORT))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
