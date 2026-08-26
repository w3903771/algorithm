"""题解本地验证 harness：用官方样例跑 solutions/ 下的题解，逐题给出通过/失败。

题解自 P-M③ 起是一题一目录 `solutions/<site>/<题号>/`，路径一律走
`scripts/sol_store.py` 查表，本文件不自己拼（08 号文件 §6.1）。

用法:
  uv run python scripts/verify.py              # 验证全部已写题解
  uv run python scripts/verify.py PIO          # 只验证前缀匹配的
  uv run python scripts/verify.py BISHI136 BISHI137
  uv run python scripts/verify.py --no-state BM1   # 只打印结果，不动共享的状态与报告
  uv run python scripts/verify.py --exact BM1      # 只跑 BM1，不按前缀连带 BM10/BM100

**两种判题模式**，按题目所属题单自动分派（题单登记在 data/_sources.json）：

  acm   读 stdin 写 stdout。把样例输入喂给 `python <题目录>/sol.py`，比对 stdout。
        BISHI / PIO 走这条。
  core  核心代码模式：题解只实现 `class Solution` 的某个方法，没有 stdin。
        由 scripts/corerun.py 在子进程里按签名喂参、取返回值，比对结构。
        BM / LC 走这条。签名来自题面 JSON 的 `func` 字段
        （力扣取自 metaData，牛客由 nc_fetch_template.py 从 Java 模板解析）。

判定规则（按各题 `meta.json` 的 `judge` 字段；P-M③ 前是全局 solutions/_judge.json）：

  acm 模式
    exact  逐行去尾空白后严格比对（默认）
    float  逐 token 比对，数值按 1e-6 相对/绝对误差
    spj    有专门校验器 <题目录>/spj.py，导出 check(inp, out) -> bool
    skip   题目本身答案不唯一且没写校验器，只检查程序不崩溃

  core 模式（比对的是**结构**不是字符串，`{3,2,1}` 与 `[3,2,1]` 判等）
    exact           默认，逐层严格比对；配 eps 时数值按相对误差
    unordered       顶层顺序无关（LC46 全排列、LC347 前 K 个高频元素）
    unordered_deep  内外层都顺序无关（LC49 字母异位词分组、LC78 子集）
    spj             同上，走 <题目录>/spj.py 的 check(inp, out)
    raw             不做方言解析，直接按原始文本比。给驱动器产出整句话的题用
                    （BM30 的期望输出是 `From left to right are:4,6;...`，
                     没加引号，按方言解析会被顶层逗号切成列表，永远比不上）
    另有 outParam：返回 void 的原地修改题，答案在第几个入参里（默认 0）
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import codec  # noqa: E402
import sol_store as store  # noqa: E402
from corerun import SENTINEL  # noqa: E402

ROOT = store.ROOT
DOCS = ROOT / "docs"
DATA = store.DATA                   # 公开数据：见 sol_store.DATA
SOL = store.SOL
REPORT = SOL / "_verify_report.md"
STATE = SOL / "_verify_state.json"
# 判题临时作业文件。P-M③ 前落在 solutions/_spj/ 下，那里现在是各题自己的目录，
# 掉进去的残留会被 git 看见；改放已 gitignore 的 .cache/。
JOBS = ROOT / ".cache" / "verify"

# 特判器与驱动器是 importlib 从**题目录里**加载的，默认会就地写 __pycache__——
# P-M③ 之前它们都落在 solutions/_spj/ 一个目录里，现在会散进 29 个入库的题目录。
# 这些字节码缓存一次性用完就没用，直接关掉。
sys.dont_write_bytecode = True

TIMEOUT = 10.0
# 子进程的输出一律按 UTF-8 编码。Windows 默认是 GBK，驱动器只要返回中文
# （LC142 的「返回索引为 1 的链表节点」就是），父进程按 UTF-8 读就会
# UnicodeDecodeError，结果被当成「没有输出」——题解明明是对的却报 NO_OUTPUT。
# PYTHONDONTWRITEBYTECODE：core 模式的 driver.py 是 corerun.py 在**子进程**里加载的，
# 父进程的 sys.dont_write_bytecode 管不到它，得靠环境变量传下去。
CHILD_ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
DIALECT = {"nowcoder": codec.NOWCODER, "leetcode": codec.LEETCODE}


def load_index() -> dict:
    """题号 -> {raw 目录, 判题模式, 序列化方言}。

    题面 JSON 不再固定在 05-nowcoder/raw 下——力扣的在 06-leetcode/raw。
    所以按 data/_sources.json 登记的题单去找，加题单不用改这里。
    """
    idx = {}
    p = DATA / "_sources.json"
    if not p.exists():
        return idx
    d = json.loads(p.read_text(encoding="utf-8"))
    for s in d["sets"]:
        raw = ROOT / s["raw"]
        if not raw.exists():
            continue
        info = {"raw": raw, "mode": s["mode"],
                "dialect": DIALECT.get(s["site"], codec.LEETCODE)}
        for f in raw.glob(f"{s['prefix']}*.json"):
            # 前缀是 BM 时别把 BISHI 也吃进来
            if re.fullmatch(rf"{s['prefix']}\d+", f.stem):
                idx[f.stem] = info
    return idx


def load_cfg() -> dict:
    """`{题号: judge 配置}`。原 solutions/_judge.json，P-M③ 起在各题 meta.json。"""
    return store.judge_cfg()


def norm_lines(s: str) -> list:
    return [ln.rstrip() for ln in s.replace("\r\n", "\n").rstrip("\n").split("\n")]


def cmp_exact(exp: str, got: str) -> bool:
    return norm_lines(exp) == norm_lines(got)


def cmp_float(exp: str, got: str, eps: float = 1e-6) -> bool:
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


def load_spj(no: str):
    p = store.spj_path(no)
    if not p.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"spj_{no}", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "check", None)


def run_core(no: str, cfg: dict, info: dict, sol: Path = None) -> dict:
    """核心代码模式：一个样例开一个子进程，按签名喂参、比对返回结构。

    `sol` 留给自测（scripts/test_corejudge.py）指向临时夹具，
    平时不传，就用该题目录里的 sol.py。
    """
    sol = sol or store.sol_path(no)
    data = json.loads((info["raw"] / f"{no}.json").read_text(encoding="utf-8"))
    func = data.get("func") or {}
    if not func or func.get("kind") == "unknown":
        return {"no": no, "status": "NO_SIGNATURE",
                "detail": "题面 JSON 里没有可用的 func 签名"}
    # 调用约定推不出来的题（要实现多个互相咬合的方法）靠自定义驱动器
    driver = store.driver_path(no)
    if func.get("kind") == "multi" and not driver.exists():
        return {"no": no, "status": "NO_DRIVER",
                "detail": f"需要 {store.driver_path(no).relative_to(ROOT).as_posix()}"}
    examples = [e for e in (data.get("examples") or []) if e.get("aligned", True)]
    if not examples:
        return {"no": no, "status": "NO_SAMPLE", "detail": "题面无可判题样例"}

    conf = cfg.get(no, {})
    mode = conf.get("mode", "exact")
    eps = float(conf.get("eps", 0.0))
    checker = load_spj(no) if mode == "spj" else None
    if mode == "spj" and checker is None:
        mode = "exact"
    cmp_fn = codec.CMP.get(mode, codec.equal)

    fails, t0 = [], time.time()
    jobfile = JOBS / f"{no}.json"                 # 已 gitignore 的缓存目录，跑完就删
    for i, ex in enumerate(examples, 1):
        jobfile.write_text(json.dumps({
            "solution": str(sol), "func": func, "dialect": info["dialect"],
            "input": ex.get("input", ""), "outParam": conf.get("outParam"),
            "driver": str(driver) if driver.exists() else None,
        }, ensure_ascii=False), encoding="utf-8")
        try:
            p = subprocess.run([sys.executable, str(ROOT / "scripts" / "corerun.py"),
                                str(jobfile)], capture_output=True, text=True,
                               timeout=TIMEOUT, encoding="utf-8", errors="replace",
                               env=CHILD_ENV)
        except subprocess.TimeoutExpired:
            fails.append((i, "TLE", ex.get("input", ""), ex.get("output", ""),
                          f"超过 {TIMEOUT}s"))
            continue
        if p.returncode != 0:
            fails.append((i, "RE", ex.get("input", ""), ex.get("output", ""),
                          (p.stderr or "")[-600:]))
            continue
        line = next((l for l in reversed((p.stdout or "").split("\n"))
                     if l.startswith(SENTINEL)), None)
        if line is None:
            fails.append((i, "NO_OUTPUT", ex.get("input", ""), ex.get("output", ""),
                          (p.stdout or "")[-400:]))
            continue
        got = json.loads(line[len(SENTINEL):])
        want = ex.get("output", "")
        if mode != "raw":
            want = codec.parse_value(want, info["dialect"])
        if mode == "raw":
            ok = " ".join(str(got).split()) == " ".join(str(want).split())
        elif mode == "spj":
            try:
                ok = bool(checker(ex.get("input", ""), got))
            except Exception as exc:
                fails.append((i, "SPJ_ERR", ex.get("input", ""), ex.get("output", ""), str(exc)))
                continue
        else:
            ok = cmp_fn(got, want, eps)
        if not ok:
            fails.append((i, "WA", ex.get("input", ""), ex.get("output", ""),
                          json.dumps(got, ensure_ascii=False)))
    if jobfile.exists():
        jobfile.unlink()

    dt = time.time() - t0
    base = {"no": no, "mode": f"core/{mode}", "cases": len(examples), "time": dt}
    return {**base, "status": "FAIL", "fails": fails} if fails else {**base, "status": "PASS"}


def run_one(no: str, cfg: dict, index: dict = None, sol: Path = None) -> dict:
    info = (index or {}).get(no)
    if info and info["mode"] == "core":
        if not (sol or store.sol_path(no)).exists():
            return {"no": no, "status": "NO_SOLUTION", "detail": "题解未写"}
        return run_core(no, cfg, info, sol)

    sol = sol or store.sol_path(no)
    raw = (info["raw"] if info else ROOT / "sources" / "05-nowcoder" / "raw") / f"{no}.json"
    if not raw.exists():
        return {"no": no, "status": "NO_PROBLEM", "detail": "缺题面 json"}
    data = json.loads(raw.read_text(encoding="utf-8"))
    examples = data.get("examples") or []
    if not examples:
        return {"no": no, "status": "NO_SAMPLE", "detail": "题面无样例"}

    mode = cfg.get(no, {}).get("mode", "exact")
    checker = load_spj(no) if mode == "spj" else None
    if mode == "spj" and checker is None:
        mode = "skip"

    cases, fails = 0, []
    t0 = time.time()
    for i, ex in enumerate(examples, 1):
        inp, exp = ex.get("input", ""), ex.get("output", "")
        if not inp.endswith("\n"):
            inp += "\n"
        try:
            p = subprocess.run([sys.executable, str(sol)], input=inp, capture_output=True,
                               text=True, timeout=TIMEOUT, encoding="utf-8",
                               errors="replace", env=CHILD_ENV)
        except subprocess.TimeoutExpired:
            fails.append((i, "TLE", inp, exp, f"超过 {TIMEOUT}s"))
            continue
        if p.returncode != 0:
            fails.append((i, "RE", inp, exp, (p.stderr or "")[-600:]))
            continue
        got = p.stdout
        cases += 1
        if mode == "exact":
            ok = cmp_exact(exp, got)
        elif mode == "float":
            ok = cmp_float(exp, got, cfg.get(no, {}).get("eps", 1e-6))
        elif mode == "spj":
            try:
                ok = bool(checker(inp, got))
            except Exception as exc:
                fails.append((i, "SPJ_ERR", inp, exp, str(exc)))
                continue
        else:  # skip
            ok = True
        if not ok:
            fails.append((i, "WA", inp, exp, got))

    dt = time.time() - t0
    if fails:
        return {"no": no, "status": "FAIL", "mode": mode, "cases": len(examples),
                "fails": fails, "time": dt}
    return {"no": no, "status": "PASS", "mode": mode, "cases": len(examples), "time": dt}


def main(argv) -> int:
    SOL.mkdir(parents=True, exist_ok=True)
    JOBS.mkdir(parents=True, exist_ok=True)
    cfg = load_cfg()

    # --no-state：多个进程并发验证各自那批题时，别去抢同一份状态文件与报告。
    # verify.py 是「读状态 -> 合并 -> 写回」，并发跑会互相覆盖甚至写坏 JSON。
    no_state = "--no-state" in argv
    # 默认按前缀匹配（`verify.py PIO` 跑整套）；--exact 只跑点名的那几题，
    # 否则 `BM1` 会把 BM10~BM19、BM100、BM101 一起带上
    exact = "--exact" in argv
    pats = [a for a in argv[1:] if not a.startswith("--")]
    sols = store.all_numbers()
    if pats:
        sols = [s for s in sols
                if any(s == p or (not exact and s.startswith(p)) for p in pats)]
    if not sols:
        print("solutions/ 下没有匹配的题解")
        return 0

    def keyf(s):
        # 按「字母前缀 + 数字」排序，否则 PIO10 会排到 PIO2 前面
        return ("".join(c for c in s if c.isalpha()),
                int("".join(c for c in s if c.isdigit()) or 0))
    sols.sort(key=keyf)

    index = load_index()
    results = [run_one(no, cfg, index) for no in sols]

    if no_state:
        for r in results:
            mark = {"PASS": "  ok  ", "FAIL": " FAIL "}.get(r["status"], f" {r['status']} ")
            print(f"[{mark}] {r['no']:<10} {r.get('mode', '-'):<12} "
                  f"{r.get('cases', '-')} 样例  {r.get('time', 0):.2f}s")
            for i, kind, inp, exp, got in (r.get("fails") or [])[:3]:
                print(f"         样例{i} {kind}  输入 {inp!r:.80}")
                print(f"           期望 {exp!r:.120}")
                print(f"           实得 {str(got)!r:.120}")
        bad = sum(r["status"] != "PASS" for r in results)
        print(f"\n通过 {len(results) - bad} / {len(results)}（--no-state，未写报告）")
        return 1 if bad else 0

    # 结果累积进状态文件：多个进程各跑一批时，报告不会被后跑的那批覆盖掉
    state = {}
    if STATE.exists():
        try:
            state = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            state = {}
    for r in results:
        state[r["no"]] = {k: v for k, v in r.items() if k != "fails"}
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def keyf2(s):
        return ("".join(c for c in s if c.isalpha()),
                int("".join(c for c in s if c.isdigit()) or 0))

    allr = [state[k] for k in sorted(state, key=keyf2)]
    npass = sum(r["status"] == "PASS" for r in allr)
    nfail = sum(r["status"] == "FAIL" for r in allr)
    other = len(allr) - npass - nfail

    L = ["# 题解本地验证报告\n",
         "> 由 `scripts/verify.py` 生成，数据为各题**官方样例**。\n",
         # 计数一律取累积 state，别混用本次运行的 results：
         # 按前缀过滤跑（如只跑 PIO）时两者题数不同，混用会写出
         # 「165 通过 0 失败 0 其它（共 18 题）」这种自相矛盾的表头
         f"**{npass} 通过　{nfail} 失败　{other} 其它**（共 {len(allr)} 题）\n",
         "| 题号 | 结果 | 判定方式 | 样例数 | 耗时 |", "| --- | --- | --- | --- | --- |"]
    icon = {"PASS": "✅ PASS", "FAIL": "❌ FAIL"}
    for r in allr:
        L.append(f"| {r['no']} | {icon.get(r['status'], '⚠️ ' + r['status'])} | "
                 f"{r.get('mode','-')} | {r.get('cases','-')} | {r.get('time',0):.2f}s |")

    bad = [r for r in results if r["status"] == "FAIL"]
    if bad:
        L.append("\n## 失败明细\n")
        for r in bad:
            L.append(f"### {r['no']}\n")
            for i, kind, inp, exp, got in r["fails"]:
                L.append(f"**样例{i} — {kind}**\n")
                L.append(f"输入\n```\n{inp.rstrip()}\n```")
                L.append(f"期望\n```\n{exp.rstrip()}\n```")
                L.append(f"实际\n```\n{str(got).rstrip()}\n```\n")
    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")

    for r in results:
        mark = {"PASS": "  ok  ", "FAIL": " FAIL "}.get(r["status"], f" {r['status']} ")
        print(f"[{mark}] {r['no']:<10} {r.get('mode','-'):<6} {r.get('cases','-')} 样例  {r.get('time',0):.2f}s")
    print(f"\n通过 {npass} / 失败 {nfail} / 其它 {other}   报告 -> {REPORT}")
    return 1 if nfail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
