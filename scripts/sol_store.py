"""题解仓库的路径与元信息访问层。

`solutions/` 自 **P-M③** 起按站点分层、一题一目录（02 号文件 §6.1）：

    solutions/<site>/<题号>/
      sol.py      Python 题解（docstring 即题解正文）
      meta.json   判题配置 ＋ 语言轨状态 ＋ 提交记录 ＋ 章节归属
      spj.py      特判校验器，可缺省
      driver.py   核心代码模式的自定义驱动器，可缺省

**「题号 → 站点」不新建映射**：读 `data/_sources.json` 的
`sets[].prefix → sets[].site`，它本来就是所有消费方共用的注册表，
接洛谷时只改那一份。所有消费方都从本模块取路径，
不要在各自脚本里再拼一遍（08 号文件 §6.1）。

**站内 URL 与目录结构解耦**：题解页仍是 `/solutions/<题号>/`，
`hooks/build_pages.py` 的 `on_files` 自己拼站内页路径，与这里的物理布局无关。

`meta.json` 的字段分两类，改动时要分清：

| 类 | 字段 | 谁是权威 |
| --- | --- | --- |
| **派生** | `site` `set` `mode` `title` `url` `topics` | `data/_sources.json`、`_problems.json`、`_mapping.json`；用 `migrate_solutions.py --sync` 重刷，别手改 |
| **权威** | `judge` `langs` | 就是这里；原 `_judge.json` / `_lang.json` / `_submit_results.json` 三份全局文件已并入并删除 |
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOL = ROOT / "solutions"
DATA = ROOT / "data"

_NUM = re.compile(r"^([A-Z]+)(\d+)$")


def sort_key(no: str):
    """按「字母前缀 + 数字」排序，否则 PIO10 会排到 PIO2 前面。"""
    m = _NUM.match(no)
    return (m.group(1), int(m.group(2))) if m else (no, 0)


def prefix_of(no: str) -> str:
    m = _NUM.match(no)
    return m.group(1) if m else ""


# --------------------------------------------------------------- 题号 → 站点

_SITE_BY_PREFIX: dict | None = None


def site_map() -> dict:
    """`{题号前缀: 站点短名}`，读 `data/_sources.json`。

    读不到就退回硬编码：本模块被构建期的 hooks 间接用到，
    整份注册表坏掉时宁可站点少个分组，也不要整站构建失败。
    """
    global _SITE_BY_PREFIX
    if _SITE_BY_PREFIX is not None:
        return _SITE_BY_PREFIX
    fallback = {"BISHI": "nowcoder", "PIO": "nowcoder",
                "BM": "nowcoder", "LC": "leetcode"}
    p = DATA / "_sources.json"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        m = {s["prefix"]: s["site"] for s in d["sets"]}
    except (ValueError, OSError, KeyError):
        m = {}
    _SITE_BY_PREFIX = m or fallback
    return _SITE_BY_PREFIX


def set_map() -> dict:
    """`{题号前缀: 题单 key}`，同样来自 `_sources.json`。"""
    p = DATA / "_sources.json"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return {s["prefix"]: s["key"] for s in d["sets"]}
    except (ValueError, OSError, KeyError):
        return {}


def site_of(no: str) -> str:
    """题号所属站点；前缀没登记就归 `other`，不抛异常。"""
    return site_map().get(prefix_of(no), "other")


# --------------------------------------------------------------- 路径

def dir_of(no: str) -> Path:
    return SOL / site_of(no) / no


def sol_path(no: str) -> Path:
    return dir_of(no) / "sol.py"


def meta_path(no: str) -> Path:
    return dir_of(no) / "meta.json"


def spj_path(no: str) -> Path:
    """特判校验器：导出 `check(inp, out) -> bool`。"""
    return dir_of(no) / "spj.py"


def driver_path(no: str) -> Path:
    """核心代码模式的自定义驱动器：导出 `run(ns, input_text, codec)`。"""
    return dir_of(no) / "driver.py"


def all_numbers() -> list:
    """磁盘上所有题号，按前缀 + 数字排序。以 `meta.json` 为准，不以 `sol.py`。"""
    if not SOL.exists():
        return []
    return sorted((p.parent.name for p in SOL.glob("*/*/meta.json")), key=sort_key)


def exists(no: str) -> bool:
    return meta_path(no).exists()


# --------------------------------------------------------------- meta 读写

def load_meta(no: str) -> dict:
    p = meta_path(no)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def save_meta(no: str, meta: dict) -> None:
    p = meta_path(no)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
                 encoding="utf-8")


def load_all() -> dict:
    """`{题号: meta}`。消费方要遍历全部题时用这个，只 glob 一次。"""
    out = {}
    for p in SOL.glob("*/*/meta.json"):
        try:
            out[p.parent.name] = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            out[p.parent.name] = {}
    return {k: out[k] for k in sorted(out, key=sort_key)}


# --------------------------------------------------------------- 常用字段

def judge_cfg(metas: dict = None) -> dict:
    """`{题号: judge 配置}`——原 `solutions/_judge.json` 的等价物。

    只回没走默认值的题，这样调用方 `cfg.get(no, {})` 的写法不用改。
    """
    metas = load_all() if metas is None else metas
    return {no: m["judge"] for no, m in metas.items() if m.get("judge")}


def submit_langs(metas: dict = None) -> dict:
    """`{题号: 提交语言}`——原 `solutions/_lang.json` 的等价物。

    默认 python3 的题不出现在结果里（原文件也是只登记例外）。
    """
    metas = load_all() if metas is None else metas
    out = {}
    for no, m in metas.items():
        v = (m.get("langs") or {}).get("py") or {}
        if v.get("submitLang"):
            out[no] = v["submitLang"]
    return out


def submit_results(metas: dict = None) -> dict:
    """`{题号: 提交记录}`——原 `solutions/_submit_results.json` 的等价物。

    只回真的提交过的题（有 `status` 的）。`submitLang` 是提交前的配置，
    不算结果，剔掉后形状与旧文件一致。
    """
    metas = load_all() if metas is None else metas
    out = {}
    for no, m in metas.items():
        v = (m.get("langs") or {}).get("py") or {}
        if v.get("status"):
            out[no] = {k: x for k, x in v.items() if k != "submitLang"}
    return out


def save_submit_result(no: str, result: dict) -> None:
    """把一次提交的判定写回该题的 `meta.json`，保留 `submitLang`。"""
    m = load_meta(no)
    langs = m.setdefault("langs", {})
    py = langs.setdefault("py", {})
    keep = py.get("submitLang")
    py.clear()
    if keep:
        py["submitLang"] = keep
    py.update(result)
    save_meta(no, m)
