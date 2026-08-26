"""P-M③：把扁平的 `solutions/` 重组成「按站点分层、一题一目录」。

    uv run python scripts/migrate_solutions.py --dry     # 只预览，不落盘
    uv run python scripts/migrate_solutions.py           # 执行迁移
    uv run python scripts/migrate_solutions.py --sync    # 只重刷 meta.json 的派生字段

搬什么（02 号文件 §6.1）：

    solutions/BISHI1.py            ->  solutions/nowcoder/BISHI1/sol.py
    solutions/_spj/BISHI26.py      ->  solutions/nowcoder/BISHI26/spj.py
    solutions/_spj/BM42_driver.py  ->  solutions/nowcoder/BM42/driver.py
    _judge.json + _lang.json + _submit_results.json  ->  各题的 meta.json

**站内 URL 不变**（08 号文件 §6.1 决策乙）：题解页仍是 `/solutions/<题号>/`，
`docs/` 里 564 处链接一处不动，也不产生重定向。

`meta.json` 的字段分派生与权威两类，见 `scripts/sol_store.py` 的模块文档字符串。
`--sync` 只重写派生的那几个，`judge` 与 `langs` 原样保留——
迁移之后 `_mapping.json` 还会在 P1②/P4/P5 改动，`topics` 得跟着重刷。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sol_store as store  # noqa: E402

ROOT = store.ROOT
SOL = store.SOL
DATA = store.DATA

OLD_JUDGE = SOL / "_judge.json"
OLD_LANG = SOL / "_lang.json"
OLD_RESULTS = SOL / "_submit_results.json"
OLD_SPJ = SOL / "_spj"

# 派生字段的权威来源在别处，`--sync` 只重写这几个键
DERIVED = ("site", "set", "mode", "title", "url", "topics")


def _load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def flat_numbers() -> list:
    """迁移前的扁平布局里有哪些题。"""
    return sorted((p.stem for p in SOL.glob("*.py") if not p.stem.startswith("_")),
                  key=store.sort_key)


def topics_index() -> dict:
    """`_mapping.json` 的「章 -> 题号」反查成「题号 -> 章 id 列表」。

    这是**派生**数据：`_mapping.json` 才是章节归属的权威，
    P1②/P4/P5 每改一次归属，都要 `--sync` 重刷一遍。
    P0b 的 `check_orphan` 读的就是这个字段（08 号文件 §4.2）。
    """
    ch = _load(DATA / "_mapping.json").get("chapters") or {}
    out = {}
    for page_id, problems in ch.items():
        for no in problems:
            out.setdefault(no, []).append(page_id)
    return {no: sorted(v) for no, v in out.items()}


def fix_note(no: str, note: str) -> str:
    """判题备注里写着旧的 `_spj/<题号>[_driver].py`，改成题目录里的相对文件名。

    备注是**给人读的**，会随 `meta.json` 一起进版本库，路径说错就等于把
    下一个维护者指到不存在的文件上（09 号文件 教训四的第三类盲区）。
    """
    return (note.replace(f"_spj/{no}_driver.py", "driver.py")
                .replace(f"_spj/{no}.py", "spj.py"))


def build_meta(no, problems, judge, langs, results, topics, old=None) -> dict:
    """拼一份 `meta.json`。`old` 非空时只覆盖派生字段（`--sync`）。"""
    info = problems.get(no) or {}
    py = {}
    if langs.get(no):
        py["submitLang"] = langs[no]
    if results.get(no):
        py.update(results[no])

    cfg = dict(judge.get(no) or {})
    if cfg.get("note"):
        cfg["note"] = fix_note(no, cfg["note"])

    meta = {
        "no": no,
        "site": store.site_of(no),
        "set": store.set_map().get(store.prefix_of(no), ""),
        "mode": info.get("mode", "acm"),
        "title": info.get("title", ""),
        "url": info.get("url", ""),
        "topics": topics.get(no, []),
        "judge": cfg,
        "langs": {"py": py} if py else {},
    }
    if old:
        merged = dict(old)
        for k in DERIVED:
            merged[k] = meta[k]
        return merged
    return meta


def fresh_meta(no: str) -> dict:
    """给**新建**的题拼一份 meta.json：没有历史提交记录，判题配置留空。

    `scripts/new_solution.py` 建骨架时调用。`sol_store.all_numbers()` 认的是
    `meta.json`——只写 sol.py 的话，这道题在所有消费方眼里都不存在。
    schema 只此一份，别在别处再拼一遍。
    """
    return build_meta(no, _load(DATA / "_problems.json"), {}, {}, {}, topics_index())


def spj_moves() -> list:
    """`_spj/` 里的文件 -> 各题目录。`<NO>.py` 是校验器，`<NO>_driver.py` 是驱动器。"""
    out = []
    if not OLD_SPJ.exists():
        return out
    for p in sorted(OLD_SPJ.glob("*.py")):
        stem = p.stem
        if stem.endswith("_driver"):
            no, dst = stem[:-len("_driver")], "driver.py"
        else:
            no, dst = stem, "spj.py"
        out.append((p, store.dir_of(no) / dst, no))
    return out


def git_mv(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["git", "mv", str(src.relative_to(ROOT)), str(dst.relative_to(ROOT))],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:            # 未入库的文件 git mv 会拒绝，退回普通搬运
        shutil.move(str(src), str(dst))


def main(argv) -> int:
    dry = "--dry" in argv
    sync = "--sync" in argv

    problems = _load(DATA / "_problems.json")
    judge = _load(OLD_JUDGE)
    langs = {k: v for k, v in _load(OLD_LANG).items() if not k.startswith("_")}
    results = _load(OLD_RESULTS)
    topics = topics_index()

    if sync:
        nos = store.all_numbers()
        changed = 0
        for no in nos:
            old = store.load_meta(no)
            new = build_meta(no, problems, judge, langs, results, topics, old)
            if new != old:
                changed += 1
                if not dry:
                    store.save_meta(no, new)
        print(f"--sync：{len(nos)} 题，派生字段有变化 {changed} 题"
              + ("（--dry，未落盘）" if dry else ""))
        return 0

    nos = flat_numbers()
    moves = spj_moves()

    # ---------------------------------------------------------- 体检
    problems_missing = [n for n in nos if n not in problems]
    unknown_site = [n for n in nos if store.site_of(n) == "other"]
    spj_orphan = [f"{p.name} -> {no}" for p, _, no in moves if no not in nos]
    judge_orphan = sorted(set(judge) - set(nos))
    lang_orphan = sorted(set(langs) - set(nos))
    result_orphan = sorted(set(results) - set(nos))
    topic_orphan = sorted(set(topics) - set(nos))
    collide = [n for n in nos if store.dir_of(n).exists()]

    by_site = {}
    for n in nos:
        by_site.setdefault(store.site_of(n), []).append(n)

    print("=" * 72)
    print("migrate_solutions" + ("  --dry" if dry else ""))
    print("=" * 72)
    print(f"扁平题解         {len(nos)}")
    for site in sorted(by_site):
        print(f"    {site:<12} {len(by_site[site])}")
    print(f"_spj/ 待归位     {len(moves)}"
          f"（校验器 {sum(1 for _, d, _ in moves if d.name == 'spj.py')}、"
          f"驱动器 {sum(1 for _, d, _ in moves if d.name == 'driver.py')}）")
    print(f"_judge.json      {len(judge)} 条")
    print(f"_lang.json       {len(langs)} 条")
    print(f"_submit_results  {len(results)} 条")
    print(f"_mapping 反查    {sum(1 for n in nos if topics.get(n))} 题有章节归属"
          f"（另 {sum(1 for n in nos if not topics.get(n))} 题为空，P1② 处理）")

    bad = 0
    for label, items in (("题号在 _problems.json 里查不到", problems_missing),
                         ("题号前缀没在 _sources.json 登记", unknown_site),
                         ("_spj/ 文件找不到对应题解", spj_orphan),
                         ("_judge.json 有多余题号", judge_orphan),
                         ("_lang.json 有多余题号", lang_orphan),
                         ("_submit_results 有多余题号", result_orphan),
                         ("_mapping.json 有多余题号", topic_orphan),
                         ("目标目录已存在", collide)):
        if items:
            bad += len(items)
            print(f"\n⚠ {label}：{len(items)}")
            for x in items[:20]:
                print(f"    {x}")
            if len(items) > 20:
                print(f"    …… 另 {len(items) - 20} 条")

    if dry:
        for sample, why in (("BISHI103", "登记了 PyPy3"), ("BM30", "raw 判定 + 驱动器")):
            print(f"\n样例 meta.json（{sample}，{why}）：")
            print(json.dumps(build_meta(sample, problems, judge, langs, results, topics),
                             ensure_ascii=False, indent=2))
        print(f"\n--dry：未落盘。体检异常 {bad} 条。")
        return 1 if bad else 0

    if bad:
        print(f"\n体检异常 {bad} 条，不执行迁移。先修干净再来。")
        return 1

    # ---------------------------------------------------------- 落盘
    for no in nos:
        git_mv(SOL / f"{no}.py", store.sol_path(no))
        store.save_meta(no, build_meta(no, problems, judge, langs, results, topics))
    for src, dst, _ in moves:
        git_mv(src, dst)

    for p in (OLD_JUDGE, OLD_LANG, OLD_RESULTS):
        if p.exists():
            r = subprocess.run(["git", "rm", "-q", str(p.relative_to(ROOT))],
                               cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
            if r.returncode != 0:
                p.unlink()
    # _spj/ 搬空后只剩 __pycache__ 之类的缓存，一并清掉
    if OLD_SPJ.exists() and not list(OLD_SPJ.glob("*.py")):
        shutil.rmtree(OLD_SPJ)

    print(f"\n落盘完成：{len(nos)} 题、{len(moves)} 个 _spj 文件，三份全局 JSON 已删除。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
